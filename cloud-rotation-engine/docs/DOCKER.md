# Docker Setup Guide

Complete Docker configuration for Cloud Rotation Engine application.

## Files Included

- **Dockerfile** - Development image with hot-reload
- **Dockerfile.prod** - Production-grade multi-stage build with gunicorn
- **docker-compose.yml** - Development environment orchestration
- **docker-compose.prod.yml** - Production environment with resource limits
- **.dockerignore** - Excludes unnecessary files from build context

---

## Quick Start (Development)

### Prerequisites
- Docker & Docker Compose installed
- AWS credentials configured (if using AWS Secrets Manager)

### Build & Run
```bash
# Build the development image
docker build -t cloud-rotation-engine:dev .

# Run with docker-compose (recommended)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Access the Application
- **API**: http://localhost:8000/api/v1
- **API Docs (Swagger)**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/docs

---

## Production Deployment

### Build Production Image
```bash
# Option 1: Using production Dockerfile
docker build -f Dockerfile.prod -t cloud-rotation-engine:latest .

# Option 2: Using docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Configuration
Create `.env` file in the cloud-rotation-engine directory:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Optional: Application settings
LOG_LEVEL=INFO
```

### Production Deployment with Resource Limits
```bash
# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d

# Monitor container
docker ps
docker stats cloud-rotation-engine-prod

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop production stack
docker-compose -f docker-compose.prod.yml down
```

---

## Image Details

### Development Image (Dockerfile)
- **Base**: python:3.11-slim
- **Size**: ~150MB (estimated)
- **Features**:
  - Hot-reload enabled (auto-restart on code changes)
  - Volume mounts for live development
  - Verbose logging

### Production Image (Dockerfile.prod)
- **Base**: python:3.11-slim
- **Size**: ~120MB (estimated, optimized with multi-stage build)
- **Features**:
  - Multi-stage build (builder + final)
  - Non-root user (security)
  - Gunicorn with 4 workers
  - Health checks
  - Optimized layers

---

## Advanced Usage

### Custom Worker Count (Production)
Modify `docker-compose.prod.yml` or override in command:

```bash
docker-compose -f docker-compose.prod.yml run \
  -e "WORKERS=8" \
  cloud-rotation-engine
```

### Port Configuration
Access on different port:

```bash
docker run -p 9000:8000 cloud-rotation-engine:latest
```

### Volume Management
Persist SQLite database:

```bash
# Create named volume
docker volume create cloud-rotation-data

# Use in compose file
volumes:
  - cloud-rotation-data:/app/data
```

### Debug Mode
Access container shell:

```bash
docker-compose exec cloud-rotation-engine /bin/bash
```

### Run Tests Inside Container
```bash
docker-compose run cloud-rotation-engine python -m pytest tests/
```

---

## Network Configuration

### Inter-Service Communication
Services are connected on `cloud-rotation-network` bridge network. Containers can communicate using service name:

```bash
# Example: From another container
curl http://cloud-rotation-engine:8000/api/v1/docs
```

### External Access
Service is exposed on host port 8000 by default for API access.

---

## Health Checks

### Manual Health Check
```bash
# Development
curl http://localhost:8000/docs

# Production (inside container)
curl http://cloud-rotation-engine-prod:8000/docs
```

### Docker Health Status
```bash
docker inspect --format='{{json .State.Health.Status}}' cloud-rotation-engine-prod
```

---

## Logging

### View Application Logs
```bash
# Development
docker-compose logs -f cloud-rotation-engine

# Production
docker-compose -f docker-compose.prod.yml logs -f cloud-rotation-engine
```

### Logs Output
- **stdout**: Application logs
- **stderr**: Error logs
- **Volume**: /app/data (SQLite database)

---

## Cleanup

### Remove Development Stack
```bash
docker-compose down
docker system prune -f  # Remove unused images/volumes
```

### Remove Production Stack
```bash
docker-compose -f docker-compose.prod.yml down
docker image rm cloud-rotation-engine:latest
```

### Full Cleanup
```bash
docker-compose down -v  # Remove volumes too
docker system prune -a --volumes
```

---

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs cloud-rotation-engine

# Inspect configuration
docker inspect cloud-rotation-engine
```

### Port Already in Use
```bash
# Find process on port 8000
lsof -i :8000

# Use different port
docker run -p 9000:8000 cloud-rotation-engine:latest
```

### AWS Credentials Not Found
```bash
# Verify env vars are set
docker-compose config | grep AWS

# Pass credentials via .env file
# Create .env with AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
```

### Database Permission Errors
```bash
# Fix data directory permissions
docker-compose exec cloud-rotation-engine \
  chmod 777 /app/data
```

---

## Performance Optimization

### Production Configuration
- **Workers**: 4 (configurable based on CPU cores)
- **Memory Limit**: 2GB (configurable)
- **CPU Limit**: 2 cores (configurable)
- **Health Check**: 30s interval, 10s timeout

### Recommended Settings for Larger Deployments
```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
    reservations:
      cpus: '2'
      memory: 2G
```

---

## Integration with Other Services

### With PostgreSQL (Optional Future)
```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: rotation_engine
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  cloud-rotation-engine:
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://user:password@postgres:5432/rotation_engine
```

---

## CI/CD Integration

### GitHub Actions Example
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: docker/build-push-action@v4
        with:
          file: ./Dockerfile.prod
          tags: cloud-rotation-engine:${{ github.sha }}
          push: true
```

---

## Security Best Practices

✅ **Implemented**:
- Non-root user in production
- Health checks
- Resource limits
- Multi-stage build optimization
- .dockerignore to exclude sensitive files

⚠️ **Recommended Additional**:
- Use image registry with authentication
- Scan images for vulnerabilities: `docker scan IMAGE`
- Keep base image updated: `docker pull python:3.11-slim`
- Use secrets management: Docker Secrets or external vault
- Enable log rotation

---

## Version Information

- **Python**: 3.11-slim
- **FastAPI**: Latest (from requirements.txt)
- **Gunicorn**: Latest (for production)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

---

For more details, see:
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
