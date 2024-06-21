FROM ubuntu:latest

# Install necessary packages
RUN apt-get update && \
    apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common

# Install Docker
RUN curl -fsSL https://get.docker.com -o get-docker.sh && \
    sh get-docker.sh

# Expose Docker daemon socket
EXPOSE 2375

# Start Docker daemon
CMD ["dockerd", "-H", "tcp://0.0.0.0:2375", "-H", "unix:///var/run/docker.sock"]
