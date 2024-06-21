import docker
import aio_pika
import json
import asyncio
import os
import shutil
import logging
from models import SessionLocal, Instance
import datetime
import subprocess
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set environment variables for Docker host
os.environ.setdefault('DOCKER_HOST', 'tcp://docker_host:2375')
docker_client = docker.from_env()

def docker_login():
    try:
        logger.info("Logging into Docker registry...")
        docker_client.login(username='alextno', password='AzsamTNO0412', registry='https://index.docker.io/v1/')
        logger.info("Logged into Docker registry successfully.")
    except docker.errors.APIError as e:
        logger.error("Docker login failed", exc_info=True)

import asyncio

async def consume_from_rabbitmq():
    while True:
        try:
            logger.info("Attempting to connect to RabbitMQ...")
            connection = await aio_pika.connect_robust("amqp://rabbitmq:5672", heartbeat=120) 
            
            async with connection:
                channel = await connection.channel()
                queue = await channel.declare_queue("instance_queue", durable=True)
                
                logger.info("Connected to RabbitMQ. Listening for messages...")
                async for message in queue:
                    async with message.process():
                        logger.info(f"Received message: {message.body.decode()}")
                        data = json.loads(message.body.decode())
                        await process_instance(data)
                        message.ack()

        except Exception as e:
            logger.error("Failed to connect or listen to RabbitMQ, retrying in 10 seconds...", exc_info=True)
            await asyncio.sleep(10)  # wait for 10 seconds before retrying


async def process_instance(data):
    instance_id = data['instance_id']
    instance_name = data['instance_name']
    module_name = data['module_name']
    github_url = data['github_url']
    file_name = data['file_name']


    logger.info(f"Processing instance '{instance_name}' with module '{module_name}'.")

    temp_dir = tempfile.mkdtemp()
    subprocess.run(['git', 'clone', github_url, temp_dir], check=True)
    source_file_path = os.path.join(temp_dir, file_name)

    if not os.path.exists(source_file_path):
        logger.error(f"File {file_name} not found in the cloned repository.")
        shutil.rmtree(temp_dir)  # Clean up the temporary directory
        return


    image_name = f"alextno/{module_name}"
    input_file_path = "/shared_data/input.json"
    shutil.copy(source_file_path, input_file_path)
    logger.info(f"File {file_name} copied to '{input_file_path}' as 'input.json'.")
    shutil.rmtree(temp_dir)
    
    prediction_script_dir = f"/shared_data/{module_name}"
    prediction_script_path = os.path.join(prediction_script_dir, 'prediction_script.py')
    requirements_prediction_path = os.path.join(prediction_script_dir, 'requirements.txt')

    if not os.path.exists(prediction_script_path):
        logger.error(f"Prediction script not found in the directory {prediction_script_dir}.")
        return

    if not os.path.exists(requirements_prediction_path):
        logger.error(f"Requirements file for prediction not found in the directory {prediction_script_dir}.")
        return

    try:
        logger.info(f"Pulling Docker image: {image_name}")
        docker_client.images.pull(image_name)
        logger.info("Image pulled successfully.")

        volumes = {'/shared_data': {'bind': '/shared_data', 'mode': 'rw'}}
        logger.info(f"Running container using image {image_name}.")
        container = docker_client.containers.run(image_name, detach=True, volumes=volumes)
        container.wait()
        container.remove(force=True)
        logger.info("Container finished execution and removed.")
        
        dockerfile_content = f"""FROM python:3.8
WORKDIR /app
COPY {module_name}/prediction_script.py /app/
COPY model.pkl /app/
COPY {module_name}/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
CMD ["python", "/app/prediction_script.py"]
"""

        dockerfile_path = "/shared_data/Dockerfile"
        with open(dockerfile_path, 'w') as dockerfile:
            dockerfile.write(dockerfile_content)

        new_image_name = f"alextno/{instance_name}"
        logger.info(f"Building new Docker image: {new_image_name}")
        docker_client.images.build(path="/shared_data", tag=new_image_name)
        logger.info("New Docker image built successfully.")

        docker_client.images.push(new_image_name)
        logger.info(f"Image {new_image_name} has been successfully pushed to the repository.")

        # Update instance status in the database
        db = SessionLocal()
        instance = db.query(Instance).filter(Instance.id == instance_id).first()
        if instance:
            instance.status = "Done"
            instance.completed_at = datetime.datetime.utcnow()
            db.commit()
            logger.info(f"Updated instance {instance_id} to 'Done' with completion datetime.")
        db.close()

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)

if __name__ == "__main__":
    docker_login()
    logger.info("Service starting...")
    loop = asyncio.get_event_loop()
    loop.create_task(consume_from_rabbitmq())
    loop.run_forever()
