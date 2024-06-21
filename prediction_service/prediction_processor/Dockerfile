# Use an official Python base image
FROM python:3.8-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the FastAPI application code to the container
COPY . .

# Run the FastAPI application using Uvicorn
CMD ["python", "worker.py"]
