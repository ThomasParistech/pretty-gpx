#!/usr/bin/python3
"""Offline regression tests for Overpass downloads and server failures."""

from collections.abc import Iterator
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

from pretty_gpx.common.request.overpass_request import download_query
from pretty_gpx.common.request.overpass_request import OVERPASS_ENDPOINTS
from pretty_gpx.common.request.overpass_request import OVERPASS_RETRY_ROUNDS
from pretty_gpx.common.request.overpass_request import OVERPASS_REQUEST_TIMEOUT


@pytest.fixture(autouse=True)
def skip_retry_waits():
    """Exercise backoff without delaying offline tests."""
    with patch('pretty_gpx.common.request.overpass_request.sleep'):
        yield


def mock_response(status: int = 200, body: bytes = b'{"elements": []}') -> MagicMock:
    """Create a streamed response with requests-style HTTP errors."""
    response = MagicMock()
    response.__enter__.return_value = response
    response.status_code = status
    response.iter_content.return_value = [body]
    if status >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(str(status), response=response)
    return response


def test_successful_download() -> None:
    """Successful requests use HTTPS and timeouts without contacting a mirror."""
    response = mock_response()
    with patch('pretty_gpx.common.request.overpass_request.requests.post', return_value=response) as post:
        assert download_query('query') == {"elements": []}
    assert post.call_count == 1
    assert post.call_args.args == (OVERPASS_ENDPOINTS[0],)
    assert post.call_args.kwargs['timeout'] == OVERPASS_REQUEST_TIMEOUT
    assert post.call_args.kwargs['data'] == {'data': 'query'}
    response.__exit__.assert_called_once()


@pytest.mark.parametrize('status', [429, 500, 502, 503, 504])
def test_transient_http_error_uses_mirror(status: int) -> None:
    """Busy or failing servers trigger one request to an independent mirror."""
    failed = mock_response(status)
    with patch('pretty_gpx.common.request.overpass_request.requests.post',
               side_effect=[failed, mock_response()]) as post:
        assert download_query('query') == {"elements": []}
    assert [call.args[0] for call in post.call_args_list] == list(OVERPASS_ENDPOINTS)
    failed.__exit__.assert_called_once()


@pytest.mark.parametrize('error', [requests.Timeout('timeout'), requests.ConnectionError('offline')])
def test_connection_failure_uses_mirror(error: requests.RequestException) -> None:
    """Network failures fall back as well as HTTP failures."""
    with patch('pretty_gpx.common.request.overpass_request.requests.post',
               side_effect=[error, mock_response()]) as post:
        assert download_query('query') == {"elements": []}
    assert post.call_count == len(OVERPASS_ENDPOINTS)


def test_interrupted_download_discards_partial_data() -> None:
    """A broken stream is closed and replaced with a complete mirror response."""
    response = mock_response()

    def interrupted_stream(chunk_size: int) -> Iterator[bytes]:
        yield b'{"elements": ['
        raise requests.ConnectionError('stream interrupted')

    response.iter_content.side_effect = interrupted_stream
    with patch('pretty_gpx.common.request.overpass_request.requests.post',
               side_effect=[response, mock_response()]):
        assert download_query('query') == {"elements": []}
    response.__exit__.assert_called_once()


def test_all_servers_fail() -> None:
    """Retries are bounded and the final error explains the map-data failure."""
    with patch('pretty_gpx.common.request.overpass_request.requests.post',
               side_effect=[mock_response(504) for _ in range(len(OVERPASS_ENDPOINTS) * OVERPASS_RETRY_ROUNDS)]) as post:
        with pytest.raises(RuntimeError, match='servers may be busy') as error:
            download_query('query')
    assert post.call_count == len(OVERPASS_ENDPOINTS) * OVERPASS_RETRY_ROUNDS
    assert isinstance(error.value.__cause__, requests.HTTPError)


def test_invalid_query_is_not_retried() -> None:
    """Query errors fail immediately instead of repeating an invalid request."""
    with patch('pretty_gpx.common.request.overpass_request.requests.post',
               return_value=mock_response(400)) as post:
        with pytest.raises(RuntimeError, match='HTTP 400'):
            download_query('query')
    assert post.call_count == 1


def test_server_remark_does_not_return_partial_data() -> None:
    """Overpass runtime errors in HTTP 200 responses cannot populate the cache."""
    response = mock_response(body=b'{"elements": [], "remark": "runtime error: Query timed out"}')
    with patch('pretty_gpx.common.request.overpass_request.requests.post', return_value=response):
        with pytest.raises(RuntimeError, match='Query timed out'):
            download_query('query')


def test_recovers_after_both_servers_fail() -> None:
    """A later round can recover without another upload."""
    with patch('pretty_gpx.common.request.overpass_request.sleep') as wait:
        with patch('pretty_gpx.common.request.overpass_request.requests.post',
                   side_effect=[mock_response(502), mock_response(504), mock_response()]) as post:
            assert download_query('query') == {"elements": []}
    assert post.call_count == 3
    wait.assert_called_once_with(5)


@pytest.mark.parametrize('body', [
    b'{"elements": [], "remark": "runtime error: Query timed out"}',
    b'<html>Bad Gateway</html>',
    b'{"unexpected": true}',
])
def test_incomplete_response_uses_mirror(body: bytes) -> None:
    """Timeout remarks and broken responses never become successful cache entries."""
    with patch('pretty_gpx.common.request.overpass_request.requests.post',
               side_effect=[mock_response(body=body), mock_response()]) as post:
        assert download_query('query') == {"elements": []}
    assert post.call_count == 2


def test_nontransient_remark_is_not_retried() -> None:
    response = mock_response(body=b'{"elements": [], "remark": "runtime error: out of memory"}')
    with patch('pretty_gpx.common.request.overpass_request.requests.post', return_value=response) as post:
        with pytest.raises(RuntimeError, match='out of memory'):
            download_query('query')
    post.assert_called_once()
