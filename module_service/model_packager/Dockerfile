# FROM python:3.8

# # Install Docker
# RUN apt-get update && apt-get install -y docker.io

# # # Set up Docker build-time variables
# # ARG DOCKER_USERNAME
# # ARG DOCKER_PASSWORD

# # (Optional) Login to Docker Hub using build-time variables
# # RUN echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

# # Set the working directory in the container
# WORKDIR /app

# # Copy the current directory contents into the container at /app
# COPY . /app

# # Install any needed dependencies specified in requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# # Define the command to run the application
# CMD ["python", "worker.py"]

# Use Docker-in-Docker base image

# Use an official Python runtime as a base image
FROM python:3.8

# Install any necessary dependencies
RUN apt-get update && apt-get install -y \
    curl

# Install Docker CLI (not the daemon)
RUN curl -fsSL https://get.docker.com -o get-docker.sh && \
    sh get-docker.sh
    
ARG DOCKER_USERNAME
ARG DOCKER_PASSWORD

# Log in to Docker Hub
RUN echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run worker.py when the container launches
CMD ["python", "worker.py"]


