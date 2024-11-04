FROM python:3.11-slim

# Set the working directory
WORKDIR /workspaces/pretty-gpx

# Copy and install system dependencies
COPY .devcontainer/packages.txt .
RUN apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y dist-upgrade && \
    xargs -a packages.txt apt-get install -y
ENV GDAL_CONFIG=/usr/bin/gdal-config

# Copy and install Python dependencies
COPY .devcontainer/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt

# Copy the application code
COPY . .

# Create the user and group before setting permissions
ENV USER=dock
ENV GROUP=sudo
RUN useradd -ms /bin/bash ${USER} && \
    usermod -aG ${GROUP} ${USER}

# Ensure the data directory exists and set permissions
RUN mkdir -p /workspaces/pretty-gpx/data && \
    chown -R ${USER}:${GROUP} /workspaces/pretty-gpx/data

# Create the MPLCONFIGDIR directory and set permissions for 'dock'
RUN mkdir -p /home/dock/.config/matplotlib && \
    chown -R ${USER}:${GROUP} /home/dock/.config/matplotlib

# Set the PYTHONPATH environment variable
ENV PYTHONPATH $PYTHONPATH:"/workspaces/pretty_gpx"

# Set the MPLCONFIGDIR environment variable
ENV MPLCONFIGDIR=/home/dock/.config/matplotlib

# Set the SERVER_HOST environment variable
ENV SERVER_HOST=0.0.0.0

# Clean up
USER root
RUN apt-get autoremove -y && \
    apt-get autoclean -y && \
    rm -rf /var/lib/apt/lists/*

# Final user
USER ${USER}