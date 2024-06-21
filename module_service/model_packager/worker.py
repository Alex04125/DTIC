import os
import subprocess
import base64
import json
import time
import asyncio
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Module
import aio_pika
import logging

# Define the SQLAlchemy engine
SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://alek:1234@mysql:3306/radiance"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create a session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Docker environment configuration
env = os.environ.copy()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def escape_quotes(content):
    return content.replace('"', '\\"')

def build_and_push_docker_image(script_content, requirements_content, module_name):
    encoded_script_content = base64.b64encode(script_content.encode()).decode()
    
    requirements_list = requirements_content.split('\n')
    requirements_list = [escape_quotes(req) for req in requirements_list]
    requirements_content = '\\n'.join(requirements_list)

    dockerfile_content = f"""
    FROM python:3.8

    WORKDIR /app

    RUN echo "{encoded_script_content}" | base64 -d > script.py
    RUN echo "{requirements_content}" > requirements.txt
    RUN pip install --no-cache-dir -r requirements.txt

    EXPOSE 3000
    CMD ["python", "script.py"]
    """

    image_tag = f"alextno/{module_name}"
    build_command = ["docker", "build", "-t", image_tag, "-"]
    try:
        subprocess.run(build_command, input=dockerfile_content, text=True, env=env, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error building Docker image: {e}")
        return

    push_command = ["docker", "push", image_tag]
    try:
        subprocess.run(push_command, env=env, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error pushing Docker image: {e}")
        return

    logger.info("Docker image built and pushed successfully")

def save_script_and_requirements(message):
    module_id = message['module_id']
    script_content = message['script_content']
    requirements_content = message['requirements_content']
    module_name = message['module_name']
    
    build_and_push_docker_image(script_content, requirements_content, module_name)
    db = SessionLocal()
    module = db.query(Module).filter(Module.id == module_id).first()
    if module:
        module.status = "done"
        module.status_updated_at = datetime.utcnow()  # Set "done" timestamp
        db.commit()
    else:
        logger.error(f"Module '{module_name}' not found in the database")
    db.close()

async def connect_to_rabbitmq():
    while True:
        try:
            connection = await aio_pika.connect_robust("amqp://rabbitmq:5672")
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ, retrying in 5 seconds: {e}")
            await asyncio.sleep(5)

async def consume_messages():
    connection = await connect_to_rabbitmq()
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue('module_queue', durable=True)
        
        async with queue.iterator() as queue_iter:
            logger.info('Waiting for messages...')
            async for message in queue_iter:
                async with message.process():
                    data = json.loads(message.body)
                    save_script_and_requirements(data)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(consume_messages())
