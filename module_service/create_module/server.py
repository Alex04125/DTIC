from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import aio_pika
import json
import tempfile
import shutil
import subprocess
import os
import time
from models import Base, Module

SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://alek:1234@mysql:3306/radiance"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
app = FastAPI()

async def connect_to_rabbitmq():
    try:
        connection = await aio_pika.connect_robust("amqp://rabbitmq:5672")
        return connection
    except Exception as e:
        print(f"Failed to connect to RabbitMQ: {e}")
        return None

async def publish_to_rabbitmq(connection, module_id, module_name, script_content, requirements_content):
    if connection is None:
        return False
    try:
        channel = await connection.channel()
        message = {
            'module_name': module_name,
            'script_content': script_content,
            'requirements_content': requirements_content,
            'module_id': module_id
        }
        await channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(message).encode()),
            routing_key='module_queue'
        )
        print(" [x] Sent message to RabbitMQ")
        await connection.close()
        return True
    except Exception as e:
        print(f"Failed to publish message: {e}")
        return False

def delete_directory_with_retry(directory, max_retries=3, delay=1):
    retries = 0
    while retries < max_retries:
        try:
            shutil.rmtree(directory)
            print("Directory deleted")
            break
        except Exception as e:
            print(f"Error deleting directory: {e}")
            retries += 1
            time.sleep(delay)

@app.post('/upload_module')
async def upload_module(json_data: dict):
    module_name = json_data.get("module_name")
    module_description = json_data.get("module_description")
    github_url = json_data.get("github_url")
    module_file_name = json_data.get("module_file_name")
    prediction_file_name = json_data.get("prediction_file_name")
    requirements_file = json_data.get("requirements_file")
    requirements_file_prediction = json_data.get("requirements_file_prediction")

    if not all([module_name, module_description, github_url, module_file_name, prediction_file_name, requirements_file, requirements_file_prediction]):
        return {"error": "All fields are required"}

    db = SessionLocal()
    if db.query(Module).filter(Module.name == module_name).first():
        db.close()
        return {"error": "A module with this name already exists"}

    temp_dir = tempfile.mkdtemp()
    try:
        subprocess.run(['git', 'clone', github_url, temp_dir], check=True)
        
        module_script_path = os.path.join(temp_dir, module_file_name)
        prediction_script_path = os.path.join(temp_dir, prediction_file_name)
        module_requirements_path = os.path.join(temp_dir, requirements_file)
        prediction_requirements_path = os.path.join(temp_dir, requirements_file_prediction)

        if not os.path.isfile(module_script_path):
            return {"error": f"The module script file '{module_file_name}' does not exist in the repository"}

        if not os.path.isfile(prediction_script_path):
            return {"error": f"The prediction script file '{prediction_file_name}' does not exist in the repository"}

        if not os.path.isfile(module_requirements_path):
            return {"error": f"The '{requirements_file}' file does not exist in the repository for the module script"}

        if not os.path.isfile(prediction_requirements_path):
            return {"error": f"The '{requirements_file_prediction}' file does not exist in the repository for the prediction script"}

        with open(module_script_path, 'rb') as script_file:
            module_script_content = script_file.read().decode('utf-8')
        with open(module_requirements_path, 'rb') as requirements_file:
            module_requirements_content = requirements_file.read().decode('utf-8')

        # Create module entry in the database
        module = Module(name=module_name, description=module_description, status="Pending")
        db.add(module)
        db.flush()  # Flush to assign ID without committing

        # Move prediction script and its requirements to shared_data/module_name directory
        shared_dir = f"/shared_data/{module_name}"
        os.makedirs(shared_dir, exist_ok=True)
        shutil.copy(prediction_script_path, os.path.join(shared_dir, "prediction_script.py"))
        shutil.copy(prediction_requirements_path, os.path.join(shared_dir, 'requirements.txt'))

        # Publish to RabbitMQ
        connection = await connect_to_rabbitmq()
        if await publish_to_rabbitmq(connection, module.id, module_name, module_script_content, module_requirements_content):
            module.status = "Not done"
            db.commit()  # Commit after successful publication
            return {"message": "Module uploaded successfully", "module_name": module_name, "module_description": module_description, "packages": module_requirements_content}
        else:
            db.rollback()  # Rollback if unable to publish
            return {"error": "Failed to connect to RabbitMQ or publish message"}
    finally:
        delete_directory_with_retry(temp_dir)
        db.close()  # Ensure the session is closed properly

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
