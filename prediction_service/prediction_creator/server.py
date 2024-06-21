from fastapi import FastAPI, HTTPException, Request
import docker
import os
import json
import aio_pika
import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Instance
from docker.errors import NotFound
import tempfile
import shutil
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Set up Docker client
os.environ.setdefault('DOCKER_HOST', 'tcp://docker_host:2375')
client = docker.from_env()

SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://alek:1234@mysql:3306/radiance"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@app.post("/get_vs_value")
async def process_request(request: Request):
    body = await request.json()
    instance_name = body.get("instance_name")
    github_url = body.get("github_url")
    file_name = body.get("file_name")

    if not all([instance_name, github_url, file_name]):
        return {"error": "instance_name, github_url, and file_name are required fields"}, 400

    shared_host_dir = '/shared_data/vs'
    shared_container_dir = '/shared_data/vs'
    input_json_path = os.path.join(shared_host_dir, 'input.json')

    db = SessionLocal()
    instance = db.query(Instance).filter_by(instance_name=instance_name).first()
    if instance is None:
        db.close()
        return {"error": "Instance name does not exist or is incorrect."}, 404

    temp_dir = tempfile.mkdtemp()
    try:
        # Clone the repository
        subprocess.run(['git', 'clone', github_url, temp_dir], check=True)
        script_path = os.path.join(temp_dir, file_name)
        if not os.path.isfile(script_path):
            return {"error": f"The script file '{file_name}' does not exist in the repository"}

        # Read input data from the file
        with open(script_path, 'r') as file:
            input_data = json.load(file)

        # Ensure shared directory exists
        if not os.path.exists(shared_host_dir):
            os.makedirs(shared_host_dir)
        
        # Copy the file to the shared directory as input.json
        with open(input_json_path, 'w') as file:
            json.dump(input_data, file)
        logger.info(f"Input data written to {input_json_path}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone repository: {e}")
        return {"error": "Failed to clone the GitHub repository"}
    finally:
        shutil.rmtree(temp_dir)
        logger.info(f"Temporary directory {temp_dir} deleted")

    try:
        container = client.containers.get(instance_name)
        instance.container_status = "Running"
        container.start()
        logger.info(f"Container {instance_name} started.")
        container.wait()
        db.commit()
        db.close()
        output_file_path = os.path.join(shared_host_dir, 'output.json')
        with open(output_file_path, 'r') as output_file:
            output_data = json.load(output_file)
        return {"success": True, "output": output_data}
    except NotFound:
        instance.container_status = "Not running"
        logger.info("Instance status not running.")
        db.commit()
        db.close()
        await publish_to_queue(instance_name)
        return {"message": "Instance is starting and being set up"}

async def publish_to_queue(instance_name):
    connection = await aio_pika.connect_robust("amqp://rabbitmq:5672")
    async with connection:
        channel = await connection.channel()
        message = {'instance_name': instance_name}
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key='prediction_queue'
        )
        logger.info("Published to queue successfully.")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
