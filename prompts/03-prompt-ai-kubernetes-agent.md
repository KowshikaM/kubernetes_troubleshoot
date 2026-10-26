# 03-prompt-ai-kubernetes-agent.md

## Goal
Build the AI Kubernetes Agent. The system should behave like a Senior Kubernetes SRE:
- Understand Kubernetes failures
- Correlate logs + events + deployment state
- Find root cause
- Suggest fixes
- Generate confidence score

Use OpenRouter API key provided via InsForge (`insforge ai setup` / `OPENROUTER_API_KEY`). Do not hardcode secrets.

## Architecture

```
Frontend
    ↓
FastAPI Backend
    ↓
Kubernetes Investigation Layer   (Prompt 02)
    ↓
AI Kubernetes Agent
    ↓
LLM Reasoning (OpenRouter via InsForge Key)
    ↓
Root Cause Analysis
    ↓
Suggested Fix
```

## Implemented Modules (backend/app/ai/)

- **prompts.py** — Prompt Builder: structured Senior-Kubernetes-SRE system prompt + evidence user prompt (trimmed to keep tokens small). Demands deterministic JSON: root_cause, explanation, fix, kubectl_commands, prevention, confidence.
- **llm.py** — LLM Client: OpenRouter chat completions via HTTPX. Timeouts, retry with backoff on 429/5xx/network errors, JSON-mode with fallback retry, graceful LLMError, no secret logging.
- **confidence.py** — Confidence Engine: blends model confidence with evidence strength (pod/deployment/event/log/network signals), caps confidence when evidence disagrees, returns reasoning strings.
- **recommender.py** — Fix Recommendation Engine: validates kubectl_commands, falls back to evidence-derived commands (describe/logs/rollout/edit) when the model returns none.
- **analyzer.py** — Root Cause Analyzer: orchestrates prompt → LLM → Diagnosis mapping; degrades to {"ok": false, reason} when the LLM is unavailable.
- **agent.py** — `analyze_cluster(cluster_data)` entry point delegating to the analyzer.

## API Integration

`POST /investigate` flow:

1. Collect Kubernetes evidence (InvestigationService)
2. Send evidence to the AI agent (`app.ai.analyzer.analyze_evidence`)
3. LLM reasoning → root cause + suggested fix
4. Return diagnosis in `InvestigateResponse.diagnosis`

Status codes:
- `success` — investigation + diagnosis complete
- `partial` — evidence collected, AI unavailable (error field explains)
- `error` — investigation failed

Example response:

```json
{
  "status": "success",
  "diagnosis": {
    "root_cause": "DATABASE_URL missing",
    "explanation": "Application cannot connect to DB.",
    "fix": "Add missing environment variable.",
    "kubectl_command": "kubectl edit deployment payment-service",
    "confidence": 92
  }
}
```

## Constraints
- Do NOT implement: authentication, investigation history, realtime updates, frontend changes, deployment.
- Keep beginner friendly, do not overengineer.
- Do NOT break existing code.

## Verification Notes
- Provision key: `npx -y @insforge/cli ai setup` (writes OPENROUTER_API_KEY to backend/.env). Blocked on free plan; use a user-provided OpenRouter key instead.
- Local testing: run uvicorn in backend/, POST /investigate with fault-injected kind cluster.
- Docker note: pass OPENROUTER_API_KEY into the backend container via compose env; the key stays server-side only.
