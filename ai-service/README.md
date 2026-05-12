# Tool-114 — AI Service

AI microservice for the **Residual Risk Calculator** capstone project.  
Built with Flask 3.x · Groq LLaMA-3.3-70b · ChromaDB · Redis · Python 3.11

---

## Architecture

```
ai-service/
├── app.py                  # Flask entry point, blueprints, security headers
├── routes/
│   ├── describe.py         # POST /describe
│   ├── recommend.py        # POST /recommend
│   ├── report.py           # POST /generate-report
│   └── health.py           # GET /health
├── services/
│   ├── groq_client.py      # Groq API wrapper (retry + backoff)
│   ├── sanitiser.py        # Input sanitisation + injection detection
│   ├── cache_service.py    # Redis AI response cache (15 min TTL)
│   └── chroma_service.py   # ChromaDB + sentence-transformers
├── prompts/
│   ├── describe_prompt.txt
│   ├── recommend_prompt.txt
│   └── report_prompt.txt
├── tests/
│   └── test_ai_service.py  # 8 pytest unit tests (Groq mocked)
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | python.org |
| pip | latest | bundled |
| Docker | 24+ | docker.com |
| Groq API Key | free tier | console.groq.com |

---

## Setup

### 1. Clone and enter the directory

```bash
git clone <repo-url>
cd ai-service
```

### 2. Create your `.env` file

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the service

```bash
python app.py
```

The service starts on **http://localhost:5000**

### 5. Run with Docker

```bash
docker build -t tool114-ai .
docker run --env-file .env -p 5000:5000 tool114-ai
```

### 6. Run with Docker Compose (full stack)

```bash
# From the project root
docker-compose up --build
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GROQ_API_KEY` | ✅ Yes | — | API key from console.groq.com |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model name |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection URL |
| `CHROMA_DATA_PATH` | No | `./chroma_data` | ChromaDB persistence path |
| `FLASK_ENV` | No | `production` | `development` enables debug mode |
| `AI_PORT` | No | `5000` | Port the service listens on |

---

## API Reference

### `GET /health`

Returns service health status, uptime, model info, and average response time.

**Response:**
```json
{
  "status": "ok",
  "model": "llama-3.3-70b-versatile",
  "uptime": "2h 14m 3s",
  "uptime_seconds": 8043,
  "avg_response_time_ms": 1240.5,
  "sample_count": 42,
  "dependencies": {
    "redis": "ok",
    "chromadb": "ok"
  },
  "timestamp": "2026-04-14T10:00:00+00:00"
}
```

---

### `POST /describe`

Analyse a risk record and return a structured description.

**Request body:**
```json
{
  "risk_name": "Unpatched Software Vulnerability",
  "category": "Cybersecurity",
  "description": "Critical systems are running software with known CVEs.",
  "likelihood": 4,
  "impact": 5,
  "existing_controls": "Vulnerability scanner; quarterly patching."
}
```

**Response:**
```json
{
  "risk_name": "Unpatched Software Vulnerability",
  "category": "Cybersecurity",
  "residual_score": 20,
  "risk_level": "CRITICAL",
  "plain_english_summary": "Critical systems with unpatched vulnerabilities...",
  "likelihood_explanation": "Likelihood rated 4 because patch cycles are slow...",
  "impact_explanation": "Impact rated 5 due to data sensitivity...",
  "control_assessment": "Existing controls are partially effective...",
  "key_drivers": ["Slow patching", "Known CVEs", "High data sensitivity"],
  "generated_at": "2026-04-14T10:00:00+00:00",
  "is_fallback": false
}
```

**Risk Level Thresholds:**

| Score | Level |
|---|---|
| 1–6 | LOW |
| 7–12 | MEDIUM |
| 13–19 | HIGH |
| 20–25 | CRITICAL |

---

### `POST /recommend`

Generate 3 actionable risk treatment recommendations.

**Request body:** Same as `/describe`

**Response:**
```json
{
  "risk_name": "Unpatched Software Vulnerability",
  "recommendations": [
    {
      "action_type": "Reduce",
      "description": "Implement automated patch management to reduce cycle time...",
      "priority": "HIGH",
      "estimated_risk_reduction": "40-50%",
      "implementation_effort": "Medium"
    },
    {
      "action_type": "Transfer",
      "description": "Obtain a cyber insurance policy covering data breach costs...",
      "priority": "MEDIUM",
      "estimated_risk_reduction": "20-30%",
      "implementation_effort": "Low"
    },
    {
      "action_type": "Accept",
      "description": "Document accepted risk with board sign-off and review quarterly...",
      "priority": "LOW",
      "estimated_risk_reduction": "0%",
      "implementation_effort": "Low"
    }
  ],
  "generated_at": "2026-04-14T10:00:00+00:00",
  "is_fallback": false
}
```

---

### `POST /generate-report`

Generate a full executive-level residual risk report.

**Request body:** Same as `/describe`, plus optional fields:
```json
{
  "...all describe fields...",
  "owner": "IT Security Team",
  "review_date": "2026-06-01"
}
```

**Response:**
```json
{
  "title": "Residual Risk Report — Unpatched Software Vulnerability",
  "report_date": "2026-04-14T10:00:00+00:00",
  "risk_level": "CRITICAL",
  "summary": "Executive summary for board presentation...",
  "overview": {
    "risk_name": "...",
    "category": "...",
    "residual_score": 20,
    "likelihood": 4,
    "impact": 5,
    "owner": "IT Security Team",
    "review_date": "2026-06-01"
  },
  "key_findings": ["Finding 1", "Finding 2", "Finding 3"],
  "control_effectiveness": "Controls are partially effective...",
  "risk_trajectory": "Stable — no significant change observed.",
  "recommendations": [
    {"action_type": "Reduce", "description": "...", "priority": "HIGH"},
    {"action_type": "Transfer", "description": "...", "priority": "MEDIUM"},
    {"action_type": "Accept", "description": "...", "priority": "LOW"}
  ],
  "conclusion": "Immediate action is required...",
  "generated_at": "2026-04-14T10:00:00+00:00",
  "is_fallback": false
}
```

---

## Error Responses

All endpoints return standard error JSON on failure:

```json
{"error": "Description of what went wrong"}
```

| Status | Meaning |
|---|---|
| 400 | Missing/invalid fields, injection detected, empty input |
| 429 | Rate limit exceeded (30 req/min per IP) |
| 500 | Unexpected server error |

When Groq is unavailable, endpoints return **200** with `"is_fallback": true` — never HTTP 500 for AI unavailability.

---

## Running Tests

Tests use mocked Groq — **no live network or API key required**.

```bash
pytest tests/ -v
```

Expected output: **8 tests passed**

---

## Security Features

- Rate limiting: 30 requests/minute per IP (flask-limiter + Redis)
- Input sanitisation: HTML stripped, prompt injection patterns blocked
- Security headers on all responses: X-Content-Type-Options, X-Frame-Options, HSTS, CSP
- No PII passed to Groq prompts
- Non-root Docker user (aiuser, UID 1001)
- All secrets via environment variables — never hardcoded

---

*Tool-114 — Residual Risk Calculator | Sprint: 14 April – 9 May 2026 | AI Developer 1*
