# Distributed Web Application — AWS EC2 + Docker + Flask

**CT5169 Fundamentals of Cloud Computing — NUI Galway (2025–2026)**

## Overview
A three-tier distributed web application that provides Wikipedia search functionality with MySQL-based caching, deployed across a local Ubuntu VM, an AWS EC2 instance, and a Dockerised database container.

## Architecture
```
User Browser
     │
Flask App (Ubuntu VM, port 5000)
     │                    │
SSH via Paramiko     MySQL 8.0 (Docker, port 7888)
     │
AWS EC2 t4g.micro
(wiki.py / Wikipedia API)
```

## Components
- **Flask** — web server handling search requests and cache logic
- **AWS EC2 (t4g.micro, Ubuntu 22.04 ARM64)** — runs Wikipedia query script via SSH
- **Docker / MySQL 8.0** — caches search results; repeat queries return instantly vs 3–5s live

## Setup

### 1. Environment variables
Copy `.env.example` to `.env` and fill in your values:
```bash
cp .env.example .env
```

### 2. Start MySQL Docker container
```bash
docker run --name mysql-cache \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  -e MYSQL_DATABASE=search_cache \
  -e MYSQL_USER=appuser \
  -e MYSQL_PASSWORD=$DB_PASSWORD \
  -p 7888:3306 -d mysql:8.0
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
python3 main.py
```
Access at `http://localhost:5000`

## Key Technical Features
- Paramiko SSH for secure VM-to-EC2 communication
- MySQL UNIQUE constraint with ON DUPLICATE KEY UPDATE for efficient cache writes
- ARM64 architecture compatibility (Apple M1 + AWS t4g.micro)
- Environment-variable-based configuration (no hardcoded credentials)
