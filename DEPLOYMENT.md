# Deployment Guide: Copilot CLI Web UI

**Version**: 0.1.0  
**Last Updated**: February 18, 2026  
**Status**: Development Setup Only (Production deployment TBD)

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Docker All-in-One Deployment](#docker-all-in-one-deployment-recommended)
- [Local Development Setup](#local-development-setup)
- [Docker Compose Deployment](#docker-compose-deployment)
- [Environment Configuration](#environment-configuration)
- [Production Considerations](#production-considerations-todo)
- [Troubleshooting](#troubleshooting)
- [Monitoring & Logging](#monitoring--logging-todo)

---

## Overview

This document describes how to deploy and run the Copilot CLI Web UI application. The application consists of:

- **Backend**: Python FastAPI application (port 8000)
- **Frontend**: Next.js React application (port 3000)
- **Infrastructure**: Docker Compose for local development

**Current Status**: Phase 1 - Local Development Only  
**Production Deployment**: To be documented in Phase 7 (T179)

---

## Docker All-in-One Deployment (Recommended)

### Easiest Way to Get Started

For the fastest setup with minimal dependencies, use the all-in-one Docker image:

```bash
# 1. Clone repository
git clone https://github.com/yourusername/copilotcli.git
cd copilotcli

# 2. Build the Docker image
./scripts/build-docker-allinone.sh

# 3. Run the container
./scripts/run-docker-allinone.sh

# 4. Access the application
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**What This Includes:**
- ✅ Complete application in one container
- ✅ Backend (Python 3.13 + FastAPI)
- ✅ Frontend (Node.js 20 + Next.js 14)
- ✅ Automatic service startup
- ✅ Persistent data storage
- ✅ GitHub feature discovery
- ✅ Local specs included

**Custom Ports:**
```bash
# Run on ports 3300 (UI) and 8800 (API)
./scripts/run-docker-allinone.sh 3300 8800
```

**Sharing With Others:**

See [DOCKER-DEPLOYMENT.md](DOCKER-DEPLOYMENT.md) for complete instructions on:
- Building and running the container
- Sharing via Docker Hub
- Sharing via image file
- Testing and verification
- Troubleshooting

---

## Prerequisites

### Required Software

| Software | Minimum Version | Purpose |
|----------|-----------------|---------|
| **Python** | 3.13.x | Backend runtime |
| **Node.js** | 20.x | Frontend runtime |
| **npm** | 10.x | Package management |
| **Docker** | 20.x | Containerization |
| **Docker Compose** | 2.x | Multi-container orchestration |
| **Git** | 2.x | Version control |

### GitHub Requirements

- **GitHub Personal Access Token (PAT)** with the following scopes:
  - `repo` (full control of private repositories)
  - `user` (read user profile data)
  - `workflow` (update GitHub Actions workflows)
  
  Generate a token at: https://github.com/settings/tokens/new

### System Requirements

- **macOS**: 10.15+ (Catalina or later)
- **Linux**: Ubuntu 20.04+ / Debian 11+ / Fedora 35+
- **Windows**: Windows 10+ with WSL2 enabled
- **RAM**: Minimum 4GB, Recommended 8GB
- **Disk**: 2GB free space for dependencies

---

## Local Development Setup

### Option 1: Native Development (Recommended for Development)

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/copilotcli.git
cd copilotcli
git checkout 009-redesigned-workflow-ux
```

#### 2. Backend Setup

```bash
# Activate virtual environment
source ./copilotcompanion/bin/activate

# Verify Python version
python --version  # Should be 3.13.x

# Install backend dependencies (if not already installed)
cd backend
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env and add your GitHub token

# Run backend server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000  
Health check: http://localhost:8000/health

#### 3. Frontend Setup

```bash
# Open new terminal
cd frontend

# Install dependencies (if not already installed)
npm install

# Create environment file
cp .env.example .env.local
# Edit .env.local if needed (defaults should work)

# Run frontend dev server
npm run dev
```

Frontend will be available at: http://localhost:3000

---

## Docker Compose Deployment

### Option 2: Docker Compose (Production-Like Environment)

#### 1. Configure Environment

```bash
# Create root .env file
cp backend/.env.example .env

# Edit .env and set required variables
nano .env
```

**Required Environment Variables**:
```bash
GITHUB_TOKEN=your_github_personal_access_token_here
SESSION_SECRET_KEY=your-random-secret-key-min-32-chars
```

#### 2. Build and Start Services

```bash
# Build images
docker-compose build

# Start all services in background
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

#### 3. Access Services

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **Backend Health**: http://localhost:8000/health

#### 4. Stop Services

```bash
# Stop services (preserves containers)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes
docker-compose down -v
```

---

## Environment Configuration

### Backend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_TOKEN` | ✅ Yes | - | GitHub Personal Access Token |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Allowed CORS origins (comma-separated) |
| `SESSION_SECRET_KEY` | ✅ Yes | `dev-secret-key-...` | Secret key for session encryption (32+ chars) |
| `SESSION_EXPIRY_HOURS` | No | `24` | Session expiration time in hours |
| `WEBSOCKET_MESSAGE_QUEUE_SIZE` | No | `1000` | Max messages in WebSocket queue |
| `COPILOT_CLI_TIMEOUT_SECONDS` | No | `300` | Max time for Copilot CLI operations |
| `LOG_LEVEL` | No | `info` | Logging level (debug/info/warning/error) |

### Frontend Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | No | `http://localhost:8000` | Backend API URL |
| `NEXT_PUBLIC_WS_URL` | No | `ws://localhost:8000/ws` | WebSocket URL |
| `NEXT_PUBLIC_APP_NAME` | No | `Copilot CLI Web UI` | Application name |
| `NEXT_PUBLIC_ENABLE_WEBSOCKET` | No | `true` | Enable WebSocket features |

**Security Note**: Never commit `.env` files to version control. Only commit `.env.example` templates.

---

## Production Considerations (TODO)

> **Note**: Production deployment guide will be completed in Phase 7 (Task T179).

### Areas to Cover (Future):

- [ ] Production server configuration (Nginx reverse proxy)
- [ ] SSL/TLS certificate setup (Let's Encrypt)
- [ ] Database migration (PostgreSQL for persistent storage)
- [ ] OAuth2 authentication (replace GitHub PAT)
- [ ] Secrets management (AWS Secrets Manager / HashiCorp Vault)
- [ ] Load balancing and horizontal scaling
- [ ] Monitoring and alerting (Prometheus + Grafana)
- [ ] Log aggregation (ELK stack / CloudWatch)
- [ ] Backup and disaster recovery
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Infrastructure as Code (Terraform / CloudFormation)

---

## Troubleshooting

### Backend Issues

#### "Module not found" errors
```bash
# Ensure you're in the virtual environment
source ./copilotcompanion/bin/activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

#### Port 8000 already in use
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn src.main:app --port 8001
```

#### GitHub API rate limiting
- Check rate limit: `curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit`
- Wait for reset time or use a different token
- Implement caching to reduce API calls

### Frontend Issues

#### "npm install" fails
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### Port 3000 already in use
```bash
# Find process using port 3000
lsof -i :3000

# Kill the process
kill -9 <PID>

# Or set a different port
PORT=3001 npm run dev
```

#### WebSocket connection fails
- Verify backend is running: `curl http://localhost:8000/health`
- Check CORS settings in `backend/.env`
- Ensure firewall allows connections on port 8000

### Docker Issues

#### "Cannot connect to Docker daemon"
```bash
# Start Docker Desktop (macOS/Windows)
# Or start Docker service (Linux)
sudo systemctl start docker
```

#### Container fails to start
```bash
# View container logs
docker-compose logs <service-name>

# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

#### Permission denied errors
```bash
# Linux only: Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

---

## Monitoring & Logging (TODO)

> **Note**: Monitoring and logging infrastructure will be implemented in Phase 7 (Tasks T185-T186).

### Planned Features:

- Application metrics (response times, error rates)
- System metrics (CPU, memory, disk usage)
- Real-time log streaming
- Error tracking and alerting
- Performance dashboards

---

## Security Checklist

### Development Environment

- [x] GitHub token stored in `.env` (not committed to git)
- [x] `.env` files added to `.gitignore`
- [x] Session secret key is random and > 32 characters
- [x] CORS configured to allow only localhost origins
- [ ] Regular dependency updates (npm audit, pip check)

### Production Environment (TODO)

- [ ] HTTPS enforced for all connections
- [ ] GitHub OAuth2 implemented (no PAT storage)
- [ ] Secrets stored in key management system
- [ ] Security headers configured (HSTS, CSP, etc.)
- [ ] Rate limiting enabled on API endpoints
- [ ] Database connections encrypted
- [ ] Regular security audits and penetration testing

---

## Support & Resources

- **Documentation**: [specs/009-redesigned-workflow-ux/](../specs/009-redesigned-workflow-ux/)
- **Issue Tracker**: GitHub Issues
- **API Documentation**: http://localhost:8000/docs (FastAPI Swagger UI)
- **Tech Stack**:
  - Backend: FastAPI 0.129.0, Python 3.13
  - Frontend: Next.js 14.0.4, React 18.2.0
  - Testing: pytest 7.4.4, Vitest 1.0.4, Playwright 1.40.1

---

**Last Updated**: February 18, 2026  
**Next Review**: After Phase 7 completion (Production deployment implementation)
