# distributed-web-app-aws-docker — Three-Tier Distributed Application

A distributed web application providing Wikipedia search with MySQL caching, built across three environments: a local Ubuntu VM running Flask, an AWS EC2 instance executing Wikipedia queries, and a Dockerised MySQL 8.0 container for response caching. Repeat queries return instantly from cache instead of hitting the API.

---

## Architecture

![Architecture](docs/architecture.svg)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web framework | Python 3.10, Flask 3.1.3 |
| Cloud compute | AWS EC2 t4g.micro, Ubuntu 22.04 ARM64 |
| Containerisation | Docker, MySQL 8.0 |
| Remote execution | Paramiko 3.0.0 (SSH) |
| Caching | MySQL — UNIQUE constraint + ON DUPLICATE KEY UPDATE |
| Virtualisation | UTM (Apple Silicon compatible) |

---

## Application Features

Users enter any search term. The first query retrieves a live Wikipedia summary via EC2. Subsequent searches for the same term return instantly from the MySQL cache.

| Feature | Detail |
|---------|--------|
| Live search | Flask → SSH → EC2 → Wikipedia API |
| Cached search | Flask → MySQL lookup → instant return |
| Visual feedback | Green badge (cached) / Blue badge (live result) |
| Cache storage | MySQL `search_cache` DB, `cache` table |

---

## System Components

### Flask App (Local Ubuntu VM — port 5000)
Handles HTTP requests, checks MySQL cache before querying EC2, saves new results to cache, and renders the search interface with cache/live badges.

### AWS EC2 t4g.micro (Ubuntu 22.04 ARM64)
Runs `wiki.py` — a Python script that queries the Wikipedia API and returns a summary. Invoked remotely by Flask via Paramiko SSH.

### Docker / MySQL 8.0 (port 7888)
Stores cached search results. A `UNIQUE` constraint on the query column prevents duplicate entries, with `ON DUPLICATE KEY UPDATE` for efficient re-caching.

---

## Key Engineering Decisions

### ARM64 architecture compatibility
The development machine is an Apple M1 Mac. VirtualBox does not support Apple Silicon.

**Solution:** Used UTM virtualisation which supports ARM64 natively. Selected Ubuntu 22.04 LTS ARM64 AMI (`ami-028f4acf86df833a8`) on EC2 to match the t4g.micro (ARM64) instance type — an x86 AMI would fail silently at launch.

### SSH key management
Copying the EC2 `.pem` key to the local VM via `scp` returned `Permission denied` when targeting the home directory directly.

**Solution:** Copied the key to `/tmp` first, then moved it with `sudo` to the intended location. The key is excluded from version control via `.gitignore`.

### Cache-first routing
Without caching, every search incurs a 3–5 second SSH round-trip to EC2 plus the Wikipedia API call.

**Solution:** Flask checks MySQL before invoking EC2. On a cache hit, the result is returned immediately with no network calls. Cache writes use `ON DUPLICATE KEY UPDATE` so re-running a query never creates duplicate rows.

### Outlook / COM authentication
The project specification called for email via Outlook on the web. The modern "new Outlook" client installed on the machine is not accessible via COM and cannot be used by UiPath or automation libraries.

**Solution:** Kept Outlook 2016 running with a pre-authenticated session. Intentionally excluded Outlook from any process-kill steps — a fresh Outlook launch with no configured profile causes authentication timeouts.

---

## What I'd add with more time

- **HTTPS / TLS** on the Flask endpoint — currently serving plain HTTP on port 5000
- **Docker Compose** to define the full stack (Flask + MySQL) as a single `docker-compose.yml`
- **Environment variable management** via `python-dotenv` for cleaner local config
- **Cache expiry** — a `cached_at` timestamp column with TTL logic so stale Wikipedia results are refreshed automatically
- **Elastic IP** so the EC2 public IP does not change on instance restart
- **Containerise Flask** — run the web server in Docker alongside MySQL for full portability

---

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

---

## Module
CT5169 — Fundamentals of Cloud Computing | University of Galway | April 2026
