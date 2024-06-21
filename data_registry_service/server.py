from fastapi import FastAPI, HTTPException, Path
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Base, Instance, Module

# Initialize FastAPI
app = FastAPI()

# Setup database connection
SQLALCHEMY_DATABASE_URL = "mysql+mysqlconnector://alek:1234@mysql:3306/radiance"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)  # Ensure tables are created at startup

@app.get("/modules")
def read_modules():
    db = SessionLocal()
    try:
        modules = db.query(Module).all()
        return [module.__dict__ for module in modules if '__dict__' in dir(module)]
    finally:
        db.close()

@app.get("/modules/{module_name}")
def read_module(module_name: str):
    db = SessionLocal()
    try:
        module = db.query(Module).filter(Module.name == module_name).first()
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")
        return module.__dict__
    finally:
        db.close()

@app.get("/instances")
def read_instances():
    db = SessionLocal()
    try:
        instances = db.query(Instance).all()
        return [instance.__dict__ for instance in instances if '__dict__' in dir(instance)]
    finally:
        db.close()

@app.get("/instances/{instance_name}")
def read_instance(instance_name: str):
    db = SessionLocal()
    try:
        instance = db.query(Instance).filter(Instance.instance_name == instance_name).first()
        if not instance:
            raise HTTPException(status_code=404, detail="Instance not found")
        return instance.__dict__
    finally:
        db.close()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)
