# AI Kubernetes Troubleshooting Agent

An on-demand AI troubleshooting system for Kubernetes clusters. The user clicks **Investigate Cluster**, the system gathers cluster state, runs AI reasoning, and returns a root-cause diagnosis with a suggested fix.

```text
Frontend
    ↓
FastAPI Backend (Orchestrator)
    ↓
Kubernetes Investigation Layer
    ↓
AI Kubernetes Agent
    ↓
LLM Reasoning (OpenRouter via InsForge)
    ↓
Root Cause + Suggested Fix
    ↓
Frontend Diagnosis
```

> **Status:** Kubernetes investigation layer **and** the AI reasoning layer are implemented. `POST /investigate` gathers structured evidence, then the AI agent (OpenRouter via the InsForge-provided key) returns a root-cause diagnosis, suggested fix, kubectl commands, prevention tips, and a confidence score.

## Tech Stack

| Layer    | Tools |
| -------- | ----- |
| Backend  | FastAPI, Python 3.12+, Uvicorn, Pydantic, Loguru, HTTPX |
| Frontend | Next.js (React), TypeScript, Tailwind CSS, Axios, React Query |
| Infra    | Docker, Docker Compose |

## Project Structure

```text
.
├── backend/            # FastAPI app (api, core, kubernetes, ai, services, models)
├── frontend/           # Next.js app (components, services, hooks, types)
├── docs/               # Documentation
├── prompts/            # Feature prompts / specs
├── docker-compose.yml  # Runs backend (:8001) + frontend (:3000)
└── README.md
```

## Quick Start (Docker)

```bash
docker compose up --build
```

Then open:

- Frontend: http://localhost:3000
- Backend health: http://localhost:8001/health (host port 8001 -> backend container 8000; 8000 is used by another local project)
- Backend API docs: http://localhost:8001/docs
- Investigate: `POST /investigate` (see below)

> The backend uses `kubectl` to inspect clusters. To investigate a real cluster, set `KUBECONFIG_PATH` (and, for Docker, mount the kubeconfig into the container). Without a reachable cluster, `/investigate` returns a clear `error` status instead of failing hard.

### Investigating a cluster

```bash
curl -X POST http://localhost:8001/investigate \
  -H "Content-Type: application/json" \
  -d '{"namespace": null}'
```

Returns structured evidence plus an AI diagnosis:

```json
{
  "status": "success",
  "investigation": {
    "pods": {},
    "logs": {},
    "events": {},
    "deployments": {},
    "network": {}
  },
  "diagnosis": {
    "root_cause": "DATABASE_URL missing",
    "explanation": "Application cannot connect to DB.",
    "fix": "Add missing environment variable.",
    "kubectl_commands": ["kubectl edit deployment payment-service"],
    "prevention": "…",
    "confidence": 92,
    "confidence_reasoning": ["…"]
  }
}
```

Response statuses:

- `success` – investigation and AI diagnosis both completed.
- `partial` – evidence collected, but AI analysis was unavailable (e.g. `OPENROUTER_API_KEY` not set or the model call failed). The `error` field explains why.
- `error` – the investigation itself failed (e.g. no reachable cluster).

## Running Locally (no Docker)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate  # macOS / Linux
pip install -r requirements.txt
cp .env.example .env         # set OPENROUTER_API_KEY (real key, e.g. sk-or-v1-...)
uvicorn app.main:app --reload --port 8001
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # set values as needed
npm run dev
```

## Environment Variables

See `.env.example` at the project root (and `backend/.env.example` / `frontend/.env.example` for the per-service copies).

| Variable                   | Used By   | Purpose                                        |
| -------------------------- | --------- | ---------------------------------------------- |
| `OPENROUTER_API_KEY`       | Backend   | OpenRouter key for AI reasoning (InsForge-provided) |
| `OPENROUTER_MODEL`         | Backend   | Default LLM model id                           |
| `KUBECONFIG_PATH`          | Backend   | Path to the kubeconfig used to reach a cluster |
| `KUBECTL_BIN`              | Backend   | kubectl binary or path (default `kubectl`)     |
| `KUBECTL_TIMEOUT_SECONDS`  | Backend   | Per-command kubectl timeout (default 30s)      |
| `NEXT_PUBLIC_API_BASE_URL` | Frontend  | Backend base URL (default `http://localhost:8001`) |
