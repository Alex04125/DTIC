# Use an official Python base image
FROM python:3.8-slim

RUN apt-get update && apt-get install -y git
# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI application code to the container
COPY . .

# Expose the port used by FastAPI
EXPOSE 8000

# Run the FastAPI application using Uvicorn
CMD ["python", "server.py", "--host", "0.0.0.0", "--port", "8000"]
