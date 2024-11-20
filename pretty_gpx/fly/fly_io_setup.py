#!/usr/bin/python3
"""Use Multiple fly.io Instances.

To allow load balancing you need to have something like sticky sessions and shared data storage;
both not trivial to implement on fly.io.

To minimize infrastructure and potential bottlenecks the implementation here takes an alternative route:
The instance simply injects its fly id into the served page so the socket connection can provide it as a
query parameter. A middleware can then decide if the requested instance id matches the one handling the
request. If not a replay must be performed.

See https://github.com/zauberzeug/nicegui/blob/main/website/fly.py
or https://github.com/zauberzeug/fly_fastapi_socketio
"""

import logging
import os
from urllib.parse import parse_qs

from nicegui import app
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.types import Receive
from starlette.types import Scope
from starlette.types import Send


def fly_io_setup() -> bool:
    """Setup fly.io specific settings.

    Returns True if running on fly.io, False otherwise.
    """
    if 'FLY_ALLOC_ID' not in os.environ:
        return False

    class FlyReplayMiddleware(BaseHTTPMiddleware):
        """Replay to correct fly.io instance.

        If the wrong instance was picked by the fly.io load balancer, we use the fly-replay header
        to repeat the request again on the right instance.

        This only works if the correct instance is provided as a query_string parameter.
        """

        def __init__(self, app: ASGIApp) -> None:
            super().__init__(app)
            self.app = app
            self.app_name = os.environ.get('FLY_APP_NAME')

        async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
            query_string = scope.get('query_string', b'').decode()
            query_params = parse_qs(query_string)
            target_instance = query_params.get('fly_instance_id', [fly_instance_id])[0]

            async def send_wrapper(message: dict) -> None:
                if target_instance != fly_instance_id and self.is_online(target_instance):
                    if message['type'] == 'websocket.close':
                        # fly.io only seems to look at the fly-replay header if websocket is accepted
                        message = {'type': 'websocket.accept'}
                    if 'headers' not in message:
                        message['headers'] = []
                    message['headers'].append([b'fly-replay', f'instance={target_instance}'.encode()])
                await send(message)
            try:
                await self.app(scope, receive, send_wrapper)  # type: ignore
            except RuntimeError as e:
                if 'No response returned.' in str(e):
                    logging.warning(f'no response returned for {scope["path"]}')
                else:
                    logging.exception('could not handle request')

        def is_online(self, fly_instance_id: str) -> bool:
            hostname = f'{fly_instance_id}.vm.{self.app_name}.internal'
            try:
                dns.resolver.resolve(hostname, 'AAAA')
                return True
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.resolver.Timeout):
                return False

    # NOTE In our global fly.io deployment we need to make sure that we connect back to the same instance.
    fly_instance_id = os.environ.get('FLY_ALLOC_ID', 'local').split('-')[0]
    app.config.socket_io_js_extra_headers['fly-force-instance-id'] = fly_instance_id  # for HTTP long polling
    app.config.socket_io_js_query_params['fly_instance_id'] = fly_instance_id  # for websocket (FlyReplayMiddleware)

    import dns.resolver  # NOTE only import on fly where we have it installed to look up if instance is still available
    app.add_middleware(FlyReplayMiddleware)  # type: ignore

    return True
