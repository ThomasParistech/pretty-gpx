
FROM python:3.10-slim

WORKDIR /workspaces/pretty-gpx

COPY ./requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt

COPY . .


RUN apt-get -y update   && \
    apt-get -y upgrade  && \
    apt-get -y install     \
    libgl1                 \
    git                    \
    libglib2.0-0          \
    tk


## Switch to non-root user
ENV USER=dock
ENV GROUP=sudo

RUN useradd -ms /bin/bash ${USER} && \
    usermod -aG ${GROUP} ${USER}

# Cleaning Part
USER root
RUN apt-get autoremove -y && \
    apt-get autoclean -y && \
    rm -rf /var/lib/apt/lists/*

# Final User
USER ${USER}