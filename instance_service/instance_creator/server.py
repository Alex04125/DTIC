from fastapi import FastAPI, Request, HTTPException
import aio_pika
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Instance, Module, Base

app = FastAPI()

SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://alek:1234@mysql:3306/radiance"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

async def connect_to_rabbitmq():
    connection = await aio_pika.connect_robust("amqp://rabbitmq:5672")
    channel = await connection.channel()
    return connection, channel

async def publish_to_rabbitmq(instance_id: int, instance_name: str, module_name: str, github_url: str, file_name: str):
    connection, channel = await connect_to_rabbitmq()
    message = {
        'instance_id': instance_id,
        'instance_name': instance_name,
        'module_name': module_name,
        'github_url': github_url,
        'file_name': file_name
    }
    await channel.default_exchange.publish(
        aio_pika.Message(body=json.dumps(message).encode()),
        routing_key='instance_queue'
    )
    print(f"[x] Sent message to RabbitMQ with instance ID: {instance_id}")
    await connection.close()

def check_module_exists(module_name: str) -> bool:
    db = SessionLocal()
    exists = db.query(Module).filter(Module.name == module_name).scalar() is not None
    db.close()
    return exists

def check_instance_name_exists(instance_name: str) -> bool:
    db = SessionLocal()
    exists = db.query(Instance).filter(Instance.instance_name == instance_name).scalar() is not None
    db.close()
    return exists

@app.post('/create_instance')
async def send_data(request: Request):
    data = await request.json()
    instance_name = data.get("instance_name")
    module_name = data.get("module_name")
    github_url = data.get("github_url")
    file_name = data.get("file_name")

    if not check_module_exists(module_name):
        return {"error": "Specified module does not exist."}

    if check_instance_name_exists(instance_name):
        return {"error": "Instance name already exists."}

    db = SessionLocal()
    instance = Instance(instance_name=instance_name, module_name=module_name, status="Not done", container_status="Not running")
    db.add(instance)
    db.commit()
    db.refresh(instance)  # Refresh to get the updated instance data including the auto-incremented ID
    instance_id = instance.id
    db.close()

    await publish_to_rabbitmq(instance_id, instance_name, module_name, github_url, file_name)

    return {
        'message': 'Data sent successfully',
        'instance_id': instance_id,
        'instance_name': instance_name,
        'module_name': module_name,
        'github_url': github_url,
        'file_name': file_name
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000)
