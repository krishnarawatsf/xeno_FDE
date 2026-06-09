# Xeno AI-Native Mini CRM

An **AI Campaign Operator for D2C brands** — helps decide who to talk to, what to say, and how to reach shoppers across WhatsApp, SMS, Email, and RCS.

## Architecture

```
Frontend (Next.js)  →  CRM Backend (FastAPI)  →  PostgreSQL + Redis
                              ↓
                    Channel Service (stub)
                              ↓
                    Async callbacks → /events/callback
```

**Event flow:** CRM sends campaign → Channel service simulates delivery (90% delivered, 70% opened, 30% clicked) → Async callbacks update analytics with idempotent event handling.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend dev)
- Optional: `OPENAI_API_KEY` for full AI features (fallbacks work without it)

### 1. Start all services

```bash
docker compose up --build
```

This starts:
- **PostgreSQL** on `5432`
- **Redis** on `6379`
- **CRM Backend** on `http://localhost:8000`
- **Channel Service** on `http://localhost:8001`

### 2. Seed demo data

```bash
curl -X POST http://localhost:8000/seed
```

### 3. Start frontend

```bash
cd frontend
cp .env.example .env.local
npm run dev
```

Open **http://localhost:3000**

## Demo Workflow

1. **Dashboard** → Click "Load Demo Data" (or `POST /seed`)
2. **Segments** → Enter "High value customers in the last 30 days" → Generate → Save
3. **Campaigns** → Create campaign with segment → AI recommend channels → Send
4. **Analytics** → Watch funnel update in real-time as events stream back

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/customers` | Ingest customer |
| GET | `/customers` | List customers |
| POST | `/customers/orders` | Ingest order |
| POST | `/segments` | Create segment |
| POST | `/segments/ai-suggest` | NL → segment definition |
| POST | `/segments/evaluate` | Evaluate segment |
| POST | `/campaigns` | Create campaign |
| POST | `/campaigns/send` | Execute campaign |
| GET | `/campaigns/:id/analytics` | Funnel metrics + AI insights |
| POST | `/campaigns/recommend` | AI channel recommendation |
| POST | `/campaigns/generate-message` | AI message generation |
| POST | `/events/callback` | Channel service webhook |
| POST | `/seed` | Load demo customers + orders |

## AI Features

- **Segment Builder** — Natural language → rule/SQL segment definition
- **Message Generator** — Personalized messages with brand tone
- **Campaign Recommender** — Channel mix + timing suggestions
- **Insight Generator** — Metrics → actionable recommendations

All AI features degrade gracefully to rule-based fallbacks when `OPENAI_API_KEY` is not set.

## Project Structure

```
xeno_FDE/
├── backend/           # FastAPI CRM core
├── channel-service/   # Stubbed messaging microservice
├── frontend/          # Next.js dashboard
└── docker-compose.yml
```

## Local Development (without Docker)

```bash
# Start Postgres + Redis (or use docker compose up postgres redis)

# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# Channel service
cd channel-service
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Frontend
cd frontend && npm run dev
```

## Design Decisions

- **Event-driven** — Channel service is treated as unreliable external system
- **Idempotency** — All callbacks use `idempotency_key` to prevent duplicates
- **Hybrid segmentation** — Rule engine + LLM-generated definitions
- **No Kafka** — Lightweight async tasks for MVP simplicity

## Deployment

### 1. Supabase (Database)

1. Create a project at [supabase.com](https://supabase.com)
2. Go to **Project Settings → Database → Connection string**
3. Copy the **Transaction pooler** URI (port `6543`) and set it as `DATABASE_URL`

### 2. Backend + Channel Service (Render)

1. Push this repo to GitHub (see below)
2. Open [Render Blueprint](https://dashboard.render.com/select-repo?type=blueprint) and connect the repo
3. Set `DATABASE_URL` to your Supabase connection string when prompted
4. After deploy, note the backend URL (e.g. `https://xeno-crm-backend.onrender.com`)
5. Run seed once: `curl -X POST https://<backend-url>/seed`

### 3. Frontend (Vercel)

1. Import the GitHub repo in [Vercel](https://vercel.com/new)
2. Set **Root Directory** to `frontend`
3. Add environment variable:
   - `NEXT_PUBLIC_API_URL` → your Render backend URL (e.g. `https://xeno-crm-backend.onrender.com`)
4. Deploy

Or via CLI:

```bash
cd frontend
vercel link
vercel env add NEXT_PUBLIC_API_URL   # paste backend URL
vercel --prod
```
