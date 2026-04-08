# Longevity OS

Personal longevity system running on a Raspberry Pi 5. Tracks biomarkers, manages evidence-based intervention protocols, and synthesises health data from Apple Health (via health-at-home bridge) and Garmin Connect.

## Stack

- **Backend:** FastAPI + SQLAlchemy 2 + SQLite
- **Frontend:** React + Vite + shadcn/ui + Recharts
- **Sync:** APScheduler (hourly), health-at-home API bridge + Garmin Connect fallback
- **Access:** Browser over Tailscale

## Setup

### 1. Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your credentials
```

### 2. Frontend

```bash
cd frontend
npm install
npm run build
```

### 3. Run (development)

```bash
# Backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Frontend (in a second terminal)
cd frontend && npm run dev
```

### 4. Run (production — systemd)

```bash
sudo cp longevity-backend.service /etc/systemd/system/
sudo cp longevity-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable longevity-backend longevity-frontend
sudo systemctl start longevity-backend longevity-frontend
```

Check status:
```bash
sudo systemctl status longevity-backend
sudo systemctl status longevity-frontend
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `GARMIN_EMAIL` | — | Garmin Connect login |
| `GARMIN_PASSWORD` | — | Garmin Connect password |
| `ANTHROPIC_API_KEY` | — | Claude API key (Phase 2) |
| `DATABASE_URL` | `sqlite:///./longevity.db` | Database path |
| `HEALTH_AT_HOME_URL` | `http://localhost:49999` | health-at-home API endpoint |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |

## Running tests

```bash
pytest
```
