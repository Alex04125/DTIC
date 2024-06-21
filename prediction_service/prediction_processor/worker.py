import docker
import aio_pika
import asyncio
import os
import json
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Instance, Base

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Setup Docker client
os.environ.setdefault('DOCKER_HOST', 'tcp://docker_host:2375')
docker_client = docker.from_env()

# Database setup
SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://alek:1234@mysql:3306/radiance"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)  # Ensure all tables are created

async def connect_to_rabbitmq():
    while True:
        try:
            connection = await aio_pika.connect_robust("amqp://rabbitmq:5672")
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ, retrying: {e}")
            await asyncio.sleep(10)  # Wait before retrying to connect

async def consume():
    connection = await connect_to_rabbitmq()  # Ensure connection is established
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue('prediction_queue', durable=True)
        logger.info("Consumer is now waiting for messages...")

        async for message in queue:
            async with message.process():
                data = json.loads(message.body)
                instance_name = data['instance_name']
                image_name = f"alextno/{instance_name}"
                shared_host_dir = '/shared_data/vs'
                shared_container_dir = '/shared_data/vs'

                logger.info(f"Processing message for instance {instance_name} with image {image_name}")
                db = SessionLocal()
                instance = db.query(Instance).filter_by(instance_name=instance_name).first()

                try:
                    docker_client.images.pull(image_name)
                    logger.info(f"Image {image_name} pulled successfully.")

                    container = docker_client.containers.run(
                        image_name,
                        name=instance_name,
                        volumes={shared_host_dir: {'bind': shared_container_dir, 'mode': 'rw'}},
                        detach=True
                    )
                    container.wait()
                    logger.info(f"Container {instance_name} started and processing completed.")

                    if instance:
                        instance.container_status = 'Running'
                        db.commit()
                        logger.info(f"Database updated: {instance_name} is running.")

                    output_file_path = os.path.join(shared_host_dir, 'output.json')
                    with open(output_file_path, 'r') as output_file:
                        output_data = json.load(output_file)
                    logger.info(f"Output from {instance_name}: {output_data}")

                except Exception as e:
                    logger.error(f"Error handling container for {instance_name}: {str(e)}")
                    db.rollback()

                finally:
                    db.close()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(consume())
