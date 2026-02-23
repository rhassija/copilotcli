# Docker Quick Reference Card

**Image Name**: `copilot-companion:allinone`  
**Last Updated**: February 22, 2026

---

## Essential Commands

### Build & Run

```bash
# Build image
./scripts/build-docker-allinone.sh

# Build without cache (clean build)
./scripts/build-docker-allinone.sh --no-cache

# Run on default ports (3000, 8000)
./scripts/run-docker-allinone.sh

# Run on custom ports
./scripts/run-docker-allinone.sh 3300 8800
```

### Container Management

```bash
# View logs (follow mode)
docker logs -f copilot-companion-allinone

# View last 50 lines
docker logs --tail 50 copilot-companion-allinone

# Check container status
docker ps | grep copilot-companion

# Stop container
docker stop copilot-companion-allinone

# Start stopped container
docker start copilot-companion-allinone

# Restart container
docker restart copilot-companion-allinone

# Remove container
docker rm -f copilot-companion-allinone
```

### Image Management

```bash
# List images
docker images | grep copilot

# Remove image
docker rmi copilot-companion:allinone

# Check image details
docker inspect copilot-companion:allinone
```

---

## Sharing Methods

### Method 1: Docker Hub

**Push to Docker Hub:**
```bash
docker login
docker tag copilot-companion:allinone yourusername/copilot-companion:latest
docker push yourusername/copilot-companion:latest
```

**Pull from Docker Hub:**
```bash
docker pull yourusername/copilot-companion:latest
docker tag yourusername/copilot-companion:latest copilot-companion:allinone
./scripts/run-docker-allinone.sh
```

### Method 2: Image File

**Save to file:**
```bash
docker save copilot-companion:allinone | gzip > copilot-companion.tar.gz
# File size: ~600-700 MB
```

**Load from file:**
```bash
gunzip -c copilot-companion.tar.gz | docker load
./scripts/run-docker-allinone.sh
```

---

## Testing & Debugging

### Health Checks

```bash
# Check backend API
curl http://localhost:8000/docs

# Check frontend
curl http://localhost:3000

# Check backend health endpoint
curl http://localhost:8000/health
```

### View Specific Logs

```bash
# Backend logs only
docker logs copilot-companion-allinone 2>&1 | grep "src\."

# Frontend logs only
docker logs copilot-companion-allinone 2>&1 | grep "Next.js"

# Discovery logs
docker logs copilot-companion-allinone 2>&1 | grep "\[Discovery\]"

# Error logs
docker logs copilot-companion-allinone 2>&1 | grep -i "error"
```

### Container Shell Access

```bash
# Enter container shell
docker exec -it copilot-companion-allinone /bin/bash

# Check files
ls -la /app/backend/
ls -la /app/frontend/
ls -la /app/specs/

# Exit shell
exit
```

---

## Troubleshooting

### Port Conflicts

```bash
# Find process using port
lsof -i :3000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different ports
./scripts/run-docker-allinone.sh 3100 8100
```

### Container Won't Start

```bash
# View full logs
docker logs copilot-companion-allinone

# Remove and recreate
docker rm -f copilot-companion-allinone
./scripts/run-docker-allinone.sh
```

### Code Changes Not Reflecting

```bash
# Rebuild without cache
./scripts/build-docker-allinone.sh --no-cache

# Remove old container and run new
docker rm -f copilot-companion-allinone
./scripts/run-docker-allinone.sh
```

### Data Persistence Issues

```bash
# Check volume mount
docker inspect copilot-companion-allinone | grep -A 10 "Mounts"

# Verify data directory
ls -la .docker-data/

# Reset data (WARNING: deletes all stored data)
docker stop copilot-companion-allinone
rm -rf .docker-data/*
docker start copilot-companion-allinone
```

---

## URLs & Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Main web UI |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Interactive Swagger UI |
| Health Check | http://localhost:8000/health | Backend health status |

---

## Feature Branch Patterns

Automatically discovers features from branches matching:

- `feature/*` - Standard feature branches
- `feat/*` - Short feature prefix
- `spec/*` - Specification branches
- `001-*`, `002-*`, etc. - Numeric-prefixed branches

**Requirements:**
- Branch must have `specs/` directory
- Directory must contain `*/spec.md` files

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FRONTEND_PORT` | `3000` | Frontend port |
| `BACKEND_PORT` | `8000` | Backend port |
| `CORS_ORIGINS` | Auto | Allowed CORS origins |

---

## Cleanup Commands

```bash
# Stop and remove container
docker rm -f copilot-companion-allinone

# Remove image
docker rmi copilot-companion:allinone

# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove all unused data (careful!)
docker system prune
```

---

## Common Scenarios

### Fresh Start

```bash
# Clone, build, run from scratch
git clone https://github.com/your-org/copilotcli.git
cd copilotcli
./scripts/build-docker-allinone.sh
./scripts/run-docker-allinone.sh
```

### Update Code

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
./scripts/build-docker-allinone.sh --no-cache
docker rm -f copilot-companion-allinone
./scripts/run-docker-allinone.sh
```

### Share with Team

```bash
# Option 1: Docker Hub
docker tag copilot-companion:allinone team/copilot:latest
docker push team/copilot:latest

# Option 2: File
docker save copilot-companion:allinone | gzip > copilot.tar.gz
# Share copilot.tar.gz file

# Option 3: Repository
# Just share GitHub repo URL, they run build script
```

### Multiple Instances

```bash
# Instance 1 (default)
docker run -d --name copilot-1 -p 3000:3000 -p 8000:8000 \
  -v "$(pwd)/.docker-data-1:/app/backend/.data" \
  copilot-companion:allinone

# Instance 2 (custom ports)
docker run -d --name copilot-2 -p 3100:3000 -p 8100:8000 \
  -v "$(pwd)/.docker-data-2:/app/backend/.data" \
  copilot-companion:allinone
```

---

## Support

- **Full Documentation**: [DOCKER-DEPLOYMENT.md](DOCKER-DEPLOYMENT.md)
- **Quick Start**: [docs/QUICKSTART.md](docs/QUICKSTART.md)
- **Troubleshooting**: Always check `docker logs copilot-companion-allinone`

---

**Pro Tips:**
- Always use `./scripts/build-docker-allinone.sh` for correct image name
- Mount `.docker-data/` volume for data persistence
- Use `--no-cache` flag when code changes aren't appearing
- Check logs first when troubleshooting: `docker logs -f copilot-companion-allinone`
