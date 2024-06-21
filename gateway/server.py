from fastapi import FastAPI, HTTPException, Request
import httpx
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# URLs for the microservices correctly formatted
UPLOAD_MODULE_SERVICE_URL = "http://create-module-service:5000/upload_module"
CREATE_INSTANCE_SERVICE_URL = "http://instance-creator-service:4000/create_instance"
GET_VS_VALUE_SERVICE_URL = "http://prediction-creator-service:8000/get_vs_value"
DATA_REGISTRY_SERVICE_URL = "http://data-registry-service:7000"


@app.post("/upload_module")
async def gateway_upload_module(request: Request):
    return await forward_request(request, UPLOAD_MODULE_SERVICE_URL)


@app.post("/create_instance")
async def gateway_create_instance(request: Request):
    return await forward_request(request, CREATE_INSTANCE_SERVICE_URL)


@app.post("/get_vs_value")
async def gateway_get_vs_value(request: Request):
    return await forward_request(request, GET_VS_VALUE_SERVICE_URL)


@app.get("/modules")
async def get_modules():
    return await forward_request_to_get(DATA_REGISTRY_SERVICE_URL + "/modules")


@app.get("/modules/{module_name}")
async def get_module(module_name: str):
    return await forward_request_to_get(
        DATA_REGISTRY_SERVICE_URL + f"/modules/{module_name}"
    )


@app.get("/instances")
async def get_instances():
    return await forward_request_to_get(DATA_REGISTRY_SERVICE_URL + "/instances")


@app.get("/instances/{instance_name}")
async def get_instance(instance_name: str):
    return await forward_request_to_get(
        DATA_REGISTRY_SERVICE_URL + f"/instances/{instance_name}"
    )


async def forward_request(request: Request, url: str):
    # try:
    data = await request.json()
    async with httpx.AsyncClient(timeout=100.0) as client:
         response = await client.post(url, json=data)
         return handle_response(response)
    # except httpx.RequestError as exc:
    #     logger.error(f"Communication error with service: {str(exc)}")
    #     raise HTTPException(
    #         status_code=503, detail=f"Error communicating with the service: {str(exc)}"
    #     )
    # except Exception as exc:
    #     logger.error(f"General error: {str(exc)}")
    #     raise HTTPException(status_code=500, detail=str(exc))


async def forward_request_to_get(url: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return handle_response(response)
    except httpx.RequestError as exc:
        logger.error(f"Communication error with service: {str(exc)}")
        raise HTTPException(
            status_code=503, detail=f"Error communicating with the service: {str(exc)}"
        )
    except Exception as exc:
        logger.error(f"General error: {str(exc)}")
        raise HTTPException(status_code=500, detail=str(exc))


def handle_response(response):
    if response.status_code == 200:
        return response.json()
    else:
        # Propagate the actual error and status code back to the client
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", "Unknown error"),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)  # Run the API gateway on port 8080
