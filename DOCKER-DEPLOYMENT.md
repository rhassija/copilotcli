# Docker All-in-One Deployment Guide

**Version**: 1.0.0  
**Last Updated**: February 22, 2026  
**Image Name**: `copilot-companion:allinone`  
**Status**: Production Ready

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Building the Image](#building-the-image)
- [Running the Container](#running-the-container)
- [Sharing the Application](#sharing-the-application)
- [Testing & Verification](#testing--verification)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)

---

## Overview

The all-in-one Docker image packages the entire Copilot Companion application (backend + frontend + dependencies) into a single container for easy deployment and sharing.

### What's Included

- **Backend**: Python 3.13 + FastAPI + Uvicorn
- **Frontend**: Node.js 20 + Next.js 14 (dev mode)
- **Specs**: Local feature specifications in `/app/specs`
- **Runtime**: Both services start automatically on container launch
- **Persistent Storage**: Volume mount for data persistence

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Docker Container: copilot-companion-allinone           │
│                                                          │
│  ┌────────────────────┐      ┌─────────────────────┐   │
│  │  Frontend (3000)   │      │  Backend (8000)     │   │
│  │  Next.js + React   │─────▶│  FastAPI + Python   │   │
│  └────────────────────┘      └─────────────────────┘   │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Persistent Storage: /app/backend/.data        │    │
│  │  (Mounted from host: .docker-data/)            │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
              │                    │
              ▼                    ▼
       Port 3000              Port 8000
       (Host)                 (Host)
```

---

## Quick Start

### For First-Time Users

```bash
# 1. Clone the repository
git clone https://github.com/your-org/copilotcli.git
cd copilotcli

# 2. Build the Docker image
./scripts/build-docker-allinone.sh

# 3. Run the container
./scripts/run-docker-allinone.sh

# 4. Open browser to http://localhost:3000
```

### For Users with Shared Image

```bash
# If you received a Docker image file (copilot-companion.tar.gz):
gunzip -c copilot-companion.tar.gz | docker load

# Or if pulling from Docker Hub:
docker pull yourusername/copilot-companion:allinone

# Run the container
cd copilotcli/scripts
./run-docker-allinone.sh
```

---

## Building the Image

### Using the Build Script (Recommended)

```bash
cd /path/to/copilotcli

# Standard build (uses Docker cache)
./scripts/build-docker-allinone.sh

# Clean build (no cache, takes longer but ensures fresh build)
./scripts/build-docker-allinone.sh --no-cache
```

**Build time**: ~2-5 minutes (first time), ~10-30 seconds (cached)

### Manual Build

```bash
cd /path/to/copilotcli

# Build with correct tag
docker build -t copilot-companion:allinone -f Dockerfile.allinone .

# Verify image was created
docker images | grep copilot-companion
```

### Build Output

You should see:
```
copilot-companion:allinone        <image-id>       1.95GB          481MB   
```

**Important**: The correct image name is `copilot-companion:allinone` (with colon, not dash)

---

## Running the Container

### Using the Run Script (Recommended)

```bash
cd /path/to/copilotcli/scripts

# Run with default ports (3000 for UI, 8000 for API)
./run-docker-allinone.sh

# Run with custom ports (e.g., 3300 for UI, 8800 for API)
./run-docker-allinone.sh 3300 8800

# Run with custom image name
./run-docker-allinone.sh 3000 8000 --image custom-image:tag
```

**Output:**
```
Starting container copilot-companion-allinone from image copilot-companion:allinone...
Container started successfully.
UI:   http://localhost:3000
API:  http://localhost:8000
Docs: http://localhost:8000/docs
```

### Manual Container Run

```bash
# Create data directory for persistence
mkdir -p .docker-data

# Run container
docker run -d \
  --name copilot-companion-allinone \
  -p 3000:3000 \
  -p 8000:8000 \
  -v "$(pwd)/.docker-data:/app/backend/.data" \
  -e "CORS_ORIGINS=http://localhost:3000" \
  copilot-companion:allinone

# View logs
docker logs -f copilot-companion-allinone
```

### Container Management

```bash
# View container status
docker ps | grep copilot-companion

# View logs (follow mode)
docker logs -f copilot-companion-allinone

# View logs (last 50 lines)
docker logs --tail 50 copilot-companion-allinone

# Stop container
docker stop copilot-companion-allinone

# Restart container
docker restart copilot-companion-allinone

# Remove container
docker rm -f copilot-companion-allinone
```

---

## Sharing the Application

### Method 1: Share via Docker Hub (Recommended)

**For the Sharer (One-time setup):**

```bash
# 1. Login to Docker Hub
docker login

# 2. Tag the image with your Docker Hub username
docker tag copilot-companion:allinone yourusername/copilot-companion:latest
docker tag copilot-companion:allinone yourusername/copilot-companion:v1.0.0

# 3. Push to Docker Hub
docker push yourusername/copilot-companion:latest
docker push yourusername/copilot-companion:v1.0.0
```

**For the Recipient:**

```bash
# 1. Pull the image
docker pull yourusername/copilot-companion:latest

# 2. Tag it locally for consistency
docker tag yourusername/copilot-companion:latest copilot-companion:allinone

# 3. Run the container
cd /path/to/copilotcli/scripts
./run-docker-allinone.sh
```

### Method 2: Share via Image File

**For the Sharer:**

```bash
# 1. Save image to compressed tar file
docker save copilot-companion:allinone | gzip > copilot-companion.tar.gz

# 2. Share copilot-companion.tar.gz via:
#    - Cloud storage (Google Drive, Dropbox, S3)
#    - USB drive
#    - Network transfer (scp, rsync)

# File size: ~600-700 MB compressed
```

**For the Recipient:**

```bash
# 1. Load the image from file
gunzip -c copilot-companion.tar.gz | docker load

# Expected output:
# Loaded image: copilot-companion:allinone

# 2. Verify image loaded
docker images | grep copilot-companion

# 3. Clone the repository (for run scripts)
git clone https://github.com/your-org/copilotcli.git
cd copilotcli/scripts

# 4. Run the container
./run-docker-allinone.sh
```

### Method 3: Share via Private Registry

```bash
# Push to private registry
docker tag copilot-companion:allinone registry.company.com/copilot-companion:latest
docker push registry.company.com/copilot-companion:latest

# Pull from private registry
docker pull registry.company.com/copilot-companion:latest
docker tag registry.company.com/copilot-companion:latest copilot-companion:allinone
```

---

## Testing & Verification

### 1. Verify Services Are Running

```bash
# Wait 10 seconds for services to start
sleep 10

# Check backend health
curl http://localhost:8000/docs
# Should return HTML (FastAPI Swagger UI)

# Check frontend
curl http://localhost:3000
# Should return HTML (Next.js page)
```

### 2. Check Container Logs

```bash
# Backend logs
docker logs copilot-companion-allinone 2>&1 | grep "Uvicorn running"
# Expected: INFO:     Uvicorn running on http://0.0.0.0:8000

# Frontend logs
docker logs copilot-companion-allinone 2>&1 | grep "Ready in"
# Expected: ✓ Ready in XXXms

# Local specs discovery
docker logs copilot-companion-allinone 2>&1 | grep "Discovered.*features from local specs"
# Expected: [Storage] Discovered X features from local specs
```

### 3. Test in Browser

1. **Open UI**: http://localhost:3000
2. **Login**: Click "Sign In with GitHub" and enter your Personal Access Token
3. **View Features**: Go to Features page - should see local specs and GitHub repos
4. **Test Discovery**: Features should include repos with specs in feature branches

### 4. Verify Persistent Storage

```bash
# Check data directory exists and has content
ls -la .docker-data/
# Should show: features_storage.json, operations_log.json (after first use)

# Restart container and verify data persists
docker restart copilot-companion-allinone
sleep 10

# Check logs - should load existing features
docker logs copilot-companion-allinone 2>&1 | grep "Loaded.*features from"
```

### 5. Test GitHub Discovery

```bash
# After logging in and visiting Features page, check logs
docker logs copilot-companion-allinone 2>&1 | grep "\[Discovery\]"

# Should see discovery logs like:
# [Discovery] owner/repo: Found X feature branches to scan: ['feature/test', '001-demo', ...]
# [Discovery] owner/repo: Scanning X branches: [...]
# [Discovery] owner/repo: Discovered X features total
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FRONTEND_PORT` | `3000` | Port for Next.js frontend |
| `BACKEND_PORT` | `8000` | Port for FastAPI backend |
| `CORS_ORIGINS` | Auto-configured | Allowed CORS origins (comma-separated) |
| `NEXT_PUBLIC_API_BASE_URL` | Auto-configured | Backend API URL for frontend |
| `NEXT_PUBLIC_WS_URL` | Auto-configured | WebSocket URL for frontend |

### Custom Port Configuration

```bash
# Run on custom ports
./run-docker-allinone.sh 4000 9000

# This automatically configures:
# - Frontend: http://localhost:4000
# - Backend: http://localhost:9000
# - CORS: http://localhost:4000
# - API Base URL: http://localhost:9000
```

### Volume Mounts

The container uses a volume mount for persistent storage:

```
Host:       .docker-data/
Container:  /app/backend/.data/

Contents:
  - features_storage.json    (discovered features)
  - operations_log.json      (operation history)
```

**To reset all data:**
```bash
docker stop copilot-companion-allinone
rm -rf .docker-data/*
docker start copilot-companion-allinone
```

---

## Troubleshooting

### Issue: "Container fails to start"

```bash
# Check logs for errors
docker logs copilot-companion-allinone 2>&1 | tail -50

# Common causes:
# - Port already in use (change ports in run script)
# - Volume mount permission issues (check .docker-data/ permissions)
# - Image corrupted (rebuild with --no-cache)
```

### Issue: "Port already in use"

```bash
# Find process using port
lsof -i :3000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or run on different ports
./run-docker-allinone.sh 3100 8100
```

### Issue: "Features not showing up"

```bash
# 1. Check if you're logged in with valid GitHub token
# 2. View discovery logs
docker logs copilot-companion-allinone 2>&1 | grep "\[Discovery\]"

# 3. Verify your branches match discovery patterns:
#    - feature/*
#    - feat/*
#    - spec/*
#    - 001-*, 002-* (numeric-prefixed)

# 4. Check branch has specs/ directory with spec.md
```

### Issue: "Changes not reflecting in container"

```bash
# Rebuild image without cache
./scripts/build-docker-allinone.sh --no-cache

# Remove old container and run new one
docker rm -f copilot-companion-allinone
./scripts/run-docker-allinone.sh
```

### Issue: "Cannot connect to backend"

```bash
# Check backend is running
curl http://localhost:8000/docs

# Check CORS configuration
docker logs copilot-companion-allinone 2>&1 | grep "CORS_ORIGINS"

# Restart container
docker restart copilot-companion-allinone
```

### Issue: "Data lost after restart"

```bash
# Verify volume mount is working
docker inspect copilot-companion-allinone | grep -A 10 "Mounts"

# Should show:
# "Source": "/path/to/.docker-data",
# "Destination": "/app/backend/.data"

# Check data directory has files
ls -la .docker-data/
```

---

## Advanced Usage

### Accessing Container Shell

```bash
# Enter container shell
docker exec -it copilot-companion-allinone /bin/bash

# Check backend files
ls -la /app/backend/

# Check frontend files
ls -la /app/frontend/

# Check local specs
ls -la /app/specs/

# Exit shell
exit
```

### Viewing Real-Time Logs

```bash
# All logs
docker logs -f copilot-companion-allinone

# Backend only
docker logs -f copilot-companion-allinone 2>&1 | grep "src\."

# Frontend only
docker logs -f copilot-companion-allinone 2>&1 | grep "Next.js"

# Discovery logs
docker logs -f copilot-companion-allinone 2>&1 | grep "\[Discovery\]"
```

### Updating Code in Running Container

```bash
# Copy updated Python file
docker cp backend/src/services/github_client.py \
  copilot-companion-allinone:/app/backend/src/services/github_client.py

# Restart container to reload
docker restart copilot-companion-allinone
```

### Custom Container Configuration

```bash
# Run with additional environment variables
docker run -d \
  --name copilot-companion-allinone \
  -p 3000:3000 \
  -p 8000:8000 \
  -v "$(pwd)/.docker-data:/app/backend/.data" \
  -e "CORS_ORIGINS=http://localhost:3000,http://192.168.1.100:3000" \
  -e "LOG_LEVEL=DEBUG" \
  copilot-companion:allinone
```

### Multi-Instance Deployment

```bash
# Instance 1 (default ports)
docker run -d --name copilot-instance-1 \
  -p 3000:3000 -p 8000:8000 \
  -v "$(pwd)/.docker-data-1:/app/backend/.data" \
  copilot-companion:allinone

# Instance 2 (custom ports)
docker run -d --name copilot-instance-2 \
  -p 3100:3000 -p 8100:8000 \
  -v "$(pwd)/.docker-data-2:/app/backend/.data" \
  -e "CORS_ORIGINS=http://localhost:3100" \
  copilot-companion:allinone
```

---

## Feature Branch Discovery Patterns

The Docker image automatically discovers features from GitHub branches matching:

| Pattern | Example | Description |
|---------|---------|-------------|
| `feature/*` | `feature/new-login` | Standard feature branches |
| `feat/*` | `feat/dashboard` | Short feature prefix |
| `spec/*` | `spec/api-v2` | Specification branches |
| `NNN-*` | `001-auth`, `002-ui` | Numeric-prefixed branches |

**Requirements:**
- Branch must contain `specs/` directory
- Directory must have `*/spec.md` files
- Repository must be accessible with your GitHub token

---

## System Requirements

### For Building

- **Docker**: 20.x or later
- **Disk Space**: 3GB free (for build process)
- **RAM**: 4GB minimum
- **Network**: Internet connection for downloading dependencies

### For Running

- **Docker**: 20.x or later
- **CPU**: 2 cores recommended
- **RAM**: 2GB minimum, 4GB recommended
- **Disk Space**: 2GB for image + storage
- **Ports**: 3000 and 8000 available (or custom ports)

---

## Security Considerations

### Production Deployment

For production use, consider:

- ✅ Use HTTPS (configure reverse proxy like Nginx)
- ✅ Use GitHub OAuth instead of Personal Access Tokens
- ✅ Store secrets in environment variables (not in image)
- ✅ Run container as non-root user
- ✅ Configure firewall rules for port access
- ✅ Regular image updates and security patches
- ✅ Implement rate limiting and authentication
- ✅ Enable container resource limits (CPU, memory)

### Development vs Production

The current Docker image is optimized for:
- ✅ Local development and testing
- ✅ Internal demos and proof-of-concepts
- ✅ Team prototyping and collaboration

For production deployment:
- ⚠️ Replace Next.js dev mode with production build
- ⚠️ Use production-grade ASGI server (Hypercorn, Gunicorn+Uvicorn)
- ⚠️ Implement proper logging and monitoring
- ⚠️ Add health checks and readiness probes
- ⚠️ Configure backup and disaster recovery

---

## Support & Resources

### Documentation

- [README.md](README.md) - Project overview
- [QUICKSTART.md](docs/QUICKSTART.md) - Getting started guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment options
- [TESTING-GUIDE.md](TESTING-GUIDE.md) - Testing instructions

### Useful Commands

```bash
# View all copilot-related images
docker images | grep copilot

# View running copilot containers
docker ps | grep copilot

# View all copilot containers (including stopped)
docker ps -a | grep copilot

# Clean up stopped containers
docker container prune

# Clean up unused images
docker image prune

# Remove specific container and image
docker rm -f copilot-companion-allinone
docker rmi copilot-companion:allinone
```

### Getting Help

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check this guide and README.md
- **Logs**: Always check `docker logs copilot-companion-allinone` for errors

---

**Last Updated**: February 22, 2026  
**Docker Image**: `copilot-companion:allinone`  
**Version**: 1.0.0  
**Status**: ✅ Production Ready for Local Development
