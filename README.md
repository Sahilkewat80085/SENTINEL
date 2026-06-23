# 🛡 SENTINEL — Git Governance & Release Readiness Dashboard

SENTINEL is an enterprise-grade Git Governance and Release Readiness Platform. It continuously analyzes Git commit history against configured deployment folders, tracking ticket coverage, propagation delays, file drift, and compliance violations to compute a real-time composite **Governance Score**.

---

## 🚀 Quick Start — Bare-Metal Execution Setup

This project runs entirely on bare-metal (no Docker). You will need to install and configure the necessary services directly on your host machine.

### Prerequisites
Make sure the following are installed and running on your machine:
1. **Python 3.12+**
2. **Node.js 18+** & `npm`
3. **PostgreSQL 16+** (Running locally on port 5432)
4. **Redis 7+** (Running locally on port 6379)
5. **Git**

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Sahilkewat80085/SENTINEL.git
cd SENTINEL
```

---

### Step 2 — Configure PostgreSQL Database

Log into your local PostgreSQL instance and create the SENTINEL database and user:

```sql
CREATE USER sentinel WITH PASSWORD 'sentinel_secure_pass';
CREATE DATABASE sentinel_db;
GRANT ALL PRIVILEGES ON DATABASE sentinel_db TO sentinel;
ALTER DATABASE sentinel_db OWNER TO sentinel;
```

---

### Step 3 — Start the Python Backend & Celery Worker

Open a new terminal window to start the FastAPI backend:

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the FastAPI Server
uvicorn app.main:app --reload --port 8000
```

Open a **second terminal window** to start the Celery worker:

```bash
cd backend
# Activate the same virtual environment
.venv\Scripts\activate
# Start the Celery Worker
celery -A app.celery_app worker --loglevel=info
```

*(Note: If you are on Windows, you may need to use `celery -A app.celery_app worker --loglevel=info --pool=solo` depending on your setup).*

---

### Step 4 — Seed the Database

With the backend running, open a **third terminal window** (with the virtual environment activated) to populate the database with real commit history and calculate the health scores:

```bash
cd backend
.venv\Scripts\activate
python -m app.core.seed
```

---

### Step 5 — Start the Next.js Frontend Dashboard

Open a **fourth terminal window** to start the frontend:

```bash
cd frontend

# Install Node.js dependencies
npm install

# Start the Next.js development server
npm run dev
```

---

### Step 6 — Open the Dashboard

Navigate to: **http://localhost:3000/**

The dashboard will open immediately (no login required) showing all your real commits, Jiras, folder health ranks, and the Governance Score.

---

## 🛑 Stop / Restart

To stop the application, press `Ctrl+C` in all four terminal windows.
To restart, you will need to re-activate the virtual environment in the backend terminals and run the start commands again.

---

## 🏗 Architecture

```
Client Browser
      │
      ▼
 Next.js Frontend :3000
      │
      ▼
 FastAPI Backend :8000 ──► PostgreSQL :5432
      │                        │
      └──► Redis :6379 ◄── Celery Worker
```

---

## 🌱 Environment Variables (Optional)

The backend uses a `.env` file (or system environment variables). Defaults are mapped in `backend/app/config.py`.

| Variable | Default | Purpose |
|----------|---------|---------|
| `GITHUB_PAT` | *(not set)* | GitHub Personal Access Token for higher rate limits (60→5000 req/hr). Optional. |
| `DATABASE_URL` | `postgresql+asyncpg://sentinel:sentinel_secure_pass@localhost:5432/sentinel_db` | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |

To set `GITHUB_PAT`:
```bash
# Windows
set GITHUB_PAT=ghp_your_token_here
uvicorn app.main:app --reload --port 8000
```
