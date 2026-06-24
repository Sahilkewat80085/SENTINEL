# 🛡 SENTINEL — Git Governance & Release Readiness Dashboard

SENTINEL is an enterprise-grade Git Governance and Release Readiness Platform. It continuously analyzes Git commit history against configured deployment folders, tracking ticket coverage, propagation delays, file drift, and compliance violations to compute a real-time composite **Governance Score**.

---

## 🚀 Quick Start — New Machine Setup

### Prerequisites
Make sure these are installed on the machine:

| Tool | Minimum Version | Check |
|------|----------------|-------|
| Docker Desktop | 4.x+ | `docker --version` |
| Git | Any | `git --version` |

> **That's it.** Everything else (Python, Node.js, PostgreSQL, Redis) runs inside Docker.

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Sahilkewat80085/SENTINEL.git
cd SENTINEL
```

---

### Step 2 — Start All Services

```bash
docker compose up -d --build
```

This builds and starts 6 containers:

| Container | Role | Port |
|-----------|------|------|
| `sentinel-nginx` | Reverse proxy / entry point | **80** |
| `sentinel-frontend` | Next.js dashboard | 3000 |
| `sentinel-backend` | FastAPI REST API | 8000 |
| `sentinel-celery` | Background task worker | — |
| `sentinel-db` | PostgreSQL 16 database | 5432 |
| `sentinel-redis` | Redis broker & cache | 6379 |

> ⏳ First build takes **5–10 minutes** (downloads images, compiles frontend). Subsequent starts take ~30 seconds.

Wait for all containers to be healthy:
```bash
docker compose ps
```
All should show `Up` status.

---

### Step 3 — Seed the Database

```bash
docker exec sentinel-backend python -m app.core.seed
```

Expected output:
```
🛡 Seeding SENTINEL database with mock data...
Seeding authors...
Syncing real commits from public GitHub API...
Synced successfully: {'synced_commits_count': 17, 'inserted_commits_count': 17, 'status': 'success'}
Refreshing materialized views...
Scanning and seeding mock hashes...
Evaluating governance rules...
Seeding daily snapshots for historical graphs...
✅ Seeding complete! SENTINEL database is now fully populated with real repo commits.
```

---

### Step 4 — Open the Dashboard

Navigate to: **http://localhost/**

The dashboard opens directly — **no login required**.

---

### Step 5 — Generate a Report

1. Click **"Reports"** in the left sidebar
2. Click **"Generate Excel Report"** or **"Generate PDF Report"**
3. The report downloads automatically to your browser

---

## 📊 Dashboard Pages

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/` | Governance Score gauge, KPIs, recent violations |
| Jira Explorer | `/jiras` | All Jiras with folder coverage status |
| Jira Detail | `/jiras/[id]` | Commit propagation timeline per ticket |
| Folders | `/folders` | Health ranking of all deployment folders |
| Folder Detail | `/folders/[name]` | Per-folder health history charts |
| Commit Log | `/commits` | Full commit history with file change details |
| Coverage Matrix | `/coverage` | Jira × Folder deployment grid |
| Content Drift | `/content` | SHA256 file consistency across folders |
| Violations | `/violations` | Active governance rule violations |
| Historical Trends | `/trends` | Coverage, health, delay charts over 30 days |
| Reports | `/reports` | Excel & PDF compliance report generator |
| Settings | `/settings` | Repository configuration & sync controls |

---

## 🛑 Stop / Restart

```bash
# Stop all containers (preserve data)
docker compose down

# Stop and wipe all data (fresh start)
docker compose down -v

# Restart a single container
docker compose restart sentinel-backend
```

---

## 🔧 Troubleshooting

**Dashboard shows no data after opening**
→ Run the seeder: `docker exec sentinel-backend python -m app.core.seed`

**Containers fail to start**
→ Check Docker Desktop is running and has enough RAM (≥4 GB recommended)
→ Check logs: `docker compose logs sentinel-backend`

**Port 80 already in use**
→ Stop whatever is using port 80, or change the nginx port in `docker-compose.yml`:
```yaml
ports:
  - "8080:80"   # access via http://localhost:8080
```

**Want to re-seed from scratch (clear all data)**
```bash
docker compose down -v
docker compose up -d
docker exec sentinel-backend python -m app.core.seed
```

---

## 🏗 Architecture

```
Client Browser
      │
      ▼
 Nginx :80
   ├── /api/v1/* ──────► FastAPI Backend :8000 ──► PostgreSQL :5432
   │                            │                        │
   │                            └──► Redis :6379 ◄── Celery Worker
   └── /* ──────────────► Next.js Frontend :3000
```

---

## 🌱 Environment Variables (Optional)

All defaults are pre-configured in `docker-compose.yml`. You only need to override these if you want to customize:

| Variable | Default | Purpose |
|----------|---------|---------|
| `GITHUB_PAT` | *(not set)* | GitHub Personal Access Token for higher rate limits (60→5000 req/hr). Optional. |
| `JWT_SECRET` | *(hardcoded)* | Change for production security |
| `DATABASE_URL` | internal | PostgreSQL connection string |

### 🔑 For Repositories with >10k Commits (GitHub Rate Limits)

When scanning large repositories with more than 10,000 commits, you will quickly hit GitHub's unauthenticated API rate limit (60 requests/hour). 

To avoid this and unlock 5,000 requests/hour, you must generate a GitHub Personal Access Token (PAT) and pass it to the docker containers:

```bash
# Windows
set GITHUB_PAT=ghp_your_token_here
docker compose up -d --build

# Linux/macOS
GITHUB_PAT=ghp_your_token_here docker compose up -d --build
```

---

## 📈 Key Features

1. **Composite Governance Score** — Grade A–F computed from folder health + severity-weighted violations
2. **Jira Coverage Matrix** — Maps Jira tickets to deployment folders showing merge status
3. **Merge Delay Analytics** — Average and P95 propagation time from staging to production
4. **SHA256 Content Drift** — Detects file configuration divergence across deployment environments
5. **10 Pluggable Governance Rules** — GOV-001 through GOV-010 with acknowledgement workflow
6. **Executive Reports** — One-click export to 9-sheet Excel or formatted PDF
7. **Historical Trends** — 30-day governance score, coverage, and delay charts
8. **Public Access** — No authentication required to view the dashboard
