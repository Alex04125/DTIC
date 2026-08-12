# DTIC

A microservice platform for packaging user-supplied ML models into Docker images and running predictions from them on demand.

You point the system at a GitHub repository containing a model script and a prediction script. DTIC clones it, builds a Docker image from the model script, pushes it to a registry, and lets you create *instances* of that module and request predictions — all through a React UI or a single API gateway.

## Architecture

```
                    ┌───────────────┐
                    │   Frontend    │  React SPA
                    └───────┬───────┘
                            v
                    ┌───────────────┐
                    │  api_gateway  │  :8080  — single entry point
                    └───────┬───────┘
        ┌───────────┬───────┴───────┬───────────────┐
        v           v               v               v
  create_module  instance_    prediction_     data_registry
     :5000        creator       creator          :7000
                  :4000          :8000        (read-only views)
        │           │               │
        │  RabbitMQ │               │  RabbitMQ
        v           v               v
  model_packager  instance_    prediction_
                  processor     processor
        └───────────┴───────────────┘
                    v
            ┌───────────────┐   ┌─────────┐
            │  docker_host  │   │  MySQL  │
            │  (DinD :2375) │   │radiance │
            └───────────────┘   └─────────┘
```

Every write path is **split into a creator and a processor**: the creator validates input, writes a row to MySQL with status `Not done`, and publishes a job to RabbitMQ. A worker consumes the job, does the slow Docker work, then flips the row to `done`. That keeps the HTTP request fast while image builds run in the background.

### Services

| Service | Port | Role |
| --- | --- | --- |
| `api_gateway` | 8080 | Forwards all client calls to the right service; propagates upstream status codes |
| `create_module` | 5000 | Validates a module upload, stages the prediction script, queues `module_queue` |
| `model_packager` | — | Worker: builds a Docker image from the model script and pushes it to the registry |
| `instance_creator` | 4000 | Creates a named instance of an existing module, queues `instance_queue` |
| `instance_processor` | — | Worker: launches the instance container via the Docker host |
| `prediction_creator` | 8000 | Clones a repo holding input JSON, hands it to the prediction container |
| `prediction_processor` | — | Worker: runs the prediction and returns the result |
| `data_registry` | 7000 | Read-only lookups for modules and instances |
| `docker_host` | 2375 | Privileged Docker-in-Docker daemon that builds and runs all generated images |
| `rabbitmq` | 5672 / 15672 | Job queues (`module_queue`, `instance_queue`) + management UI |
| `mysql` | 3306 | `radiance` database — `module_registry` and `instance_registry` tables |

Services share files through a `shared_data` Docker volume — `create_module` drops each module's `prediction_script.py` and `requirements.txt` into `/shared_data/<module_name>/` for the prediction services to pick up later.

### Data model

`data_registry_service/models.py` defines two tables:

- **`module_registry`** — `name` (unique), `description`, `status`, `created_at`, `status_updated_at`
- **`instance_registry`** — `instance_name`, `module_name`, `status`, `container_status`, `created_at`, `completed_at`

## API

All endpoints go through the gateway on port 8080.

| Method | Endpoint | Body / Purpose |
| --- | --- | --- |
| `POST` | `/upload_module` | `module_name`, `module_description`, `github_url`, `module_file_name`, `prediction_file_name`, `requirements_file`, `requirements_file_prediction` |
| `POST` | `/create_instance` | `instance_name`, `module_name`, `github_url`, `file_name` |
| `POST` | `/get_vs_value` | `instance_name`, `github_url`, `file_name` — runs a prediction |
| `GET` | `/modules` | List all modules |
| `GET` | `/modules/{module_name}` | One module |
| `GET` | `/instances` | List all instances |
| `GET` | `/instances/{instance_name}` | One instance |

Every field on `POST /upload_module` is required, and the named files must actually exist in the referenced GitHub repository or the request is rejected.

## Running it

### Docker Compose (local)

The compose file expects the images to be built locally first — it references `image:` tags with no `build:` context.

```bash
# Build the Docker-in-Docker host
docker build -t host:latest ./Host

# Build each service (repeat per service directory)
docker build -t api_gateway:latest ./gateway
docker build -t create_module:latest ./module_service/create_module
docker build -t instance_creator:latest ./instance_service/instance_creator
docker build -t instance_processor:latest ./instance_service/instance_processor
docker build -t prediction_creator:latest ./prediction_service/prediction_creator
docker build -t prediction_processor:latest ./prediction_service/prediction_processor
docker build -t data_registry:latest ./data_registry_service

# model_packager needs registry credentials to push generated images
docker build --build-arg DOCKER_USERNAME=<user> --build-arg DOCKER_PASSWORD=<pass> \
  -t model_packager:latest ./module_service/model_packager

docker compose up -d
```

Then open the gateway at `http://localhost:8080`, RabbitMQ's UI at `http://localhost:15672`.

### Frontend

```bash
cd Frontend
npm install
npm start
```

A React 18 SPA (`react-router-dom`, `styled-components`, `axios`) with pages for uploading a module, creating an instance, requesting a prediction, and browsing modules/instances. `setupProxy.js` proxies API calls to the gateway in development.

### Kubernetes

Each service ships manifests under its own `manifests/` directory, plus persistent volume definitions in `Host/persistent-storage/`, `mysql/manifests/`, and `rabbitmq/manifests/`. Apply them per service, or all at once:

```bash
kubectl apply -R -f .
```

Ingress for the gateway and frontend lives in `gateway/manifests/ingress.yaml` and `Frontend/manifests/frontend-ingress.yaml`.

## Repository layout

```
Frontend/                     React SPA + Dockerfile + manifests
gateway/                      API gateway (FastAPI)
module_service/
  create_module/              Upload endpoint
  model_packager/             Image build/push worker
instance_service/
  instance_creator/           Instance endpoint
  instance_processor/         Container launch worker
prediction_service/
  prediction_creator/         Prediction endpoint
  prediction_processor/       Prediction worker
data_registry_service/        Read-only registry API + SQLAlchemy models
Host/                         Docker-in-Docker image
mysql/  rabbitmq/             Infrastructure manifests
docker-compose.yaml
```

## Caveats

This is a prototype, and a few things need attention before it goes anywhere near production:

- **Credentials are hardcoded.** The MySQL DSN `mysql+mysqlconnector://alek:1234@mysql:3306/radiance` is repeated across services, and `docker-compose.yaml` sets `MYSQL_ROOT_PASSWORD: 1234`. Move these to environment variables or secrets.
- **`docker_host` runs privileged and exposes the Docker API unauthenticated** on port 2375. Anyone who can reach that port controls the host's Docker daemon.
- **Arbitrary code execution is the feature.** The platform clones user-supplied GitHub repos and builds/runs their code. Only accept input from trusted users, or sandbox it properly.
- **Virtualenvs are committed** (`gateway/gateway_env/`, `*/instance_creator/`, etc.). They bloat the repo and break checkouts on Windows because of path-length limits — they should be removed and added to `.gitignore`.
- **The image tag prefix is hardcoded** to `alextno/<module_name>` in `model_packager/worker.py`.
- Error handling in the gateway's `forward_request` is commented out, so upstream connection failures surface as unhandled exceptions rather than a clean 503.
