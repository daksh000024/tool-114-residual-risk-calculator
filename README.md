# Tool-114 — Residual Risk Calculator

AI-powered residual risk management tool built as an internship capstone project.

```
Team: 5 Members | Sprint: 14 April – 9 May 2026 | Demo Day: 9 May 2026
```

---

## Architecture

```
                        ┌─────────────────────────────────┐
                        │         Docker Network           │
                        │                                  │
  Browser ──► :80 ──►  │  Frontend (React+Vite+Nginx)     │
                        │         │                        │
                        │         ▼                        │
                        │  Backend (Spring Boot :8080)     │
                        │    │            │                │
                        │    ▼            ▼                │
                        │  PostgreSQL   Redis              │
                        │    :5432      :6379              │
                        │         │                        │
                        │         ▼                        │
                        │  AI Service (Flask :5000)        │
                        │    │        │        │           │
                        │  Groq    Redis    ChromaDB       │
                        └─────────────────────────────────┘
```

| Service     | Port | Technology                    |
|-------------|------|-------------------------------|
| Frontend    | 80   | React 18 + Vite + Nginx       |
| Backend     | 8080 | Java 17 + Spring Boot 3       |
| AI Service  | 5000 | Python 3.11 + Flask 3         |
| PostgreSQL  | 5432 | PostgreSQL 15                 |
| Redis       | 6379 | Redis 7                       |

---

## Prerequisites

| Tool       | Version | Install                    |
|------------|---------|----------------------------|
| Docker     | 24+     | docker.com/get-docker      |
| Docker Compose | V2+ | included with Docker Desktop |
| Git        | 2+      | git-scm.com                |
| Groq API Key | free | console.groq.com           |

---

## Setup & Run

### 1. Clone the repository

```bash
git clone <repository-url-shared-by-mentor>
cd tool-114
```

### 2. Create your .env file

```bash
cp .env.example .env
```

Open `.env` and fill in every value marked `REQUIRED`:

```
POSTGRES_PASSWORD=your_strong_password
JWT_SECRET=your_64_char_random_secret
GROQ_API_KEY=gsk_your_groq_key_here
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=your_gmail_app_password
```

> Get your free Groq API key at https://console.groq.com — no credit card needed.

### 3. Start everything

```bash
docker-compose up --build
```

First run takes 3–5 minutes (downloads images, builds services, loads AI model).

### 4. Verify all services are healthy

```bash
docker-compose ps
```

All 5 services should show `healthy` or `running`.

### 5. Access the application

| What              | URL                                    |
|-------------------|----------------------------------------|
| Frontend (UI)     | http://localhost                       |
| Backend API       | http://localhost:8080                  |
| Swagger UI        | http://localhost:8080/swagger-ui.html  |
| AI Service Health | http://localhost:5000/health           |

---

## Daily Reset (Demo Day procedure)

```bash
# Wipe all data and reseed fresh demo records
docker-compose down -v
docker-compose up --build
```

---

## Run Tests

### AI Service tests (no live network or API key needed)

```bash
# Option A: via Docker
docker-compose exec ai-service pytest tests/ -v

# Option B: locally
cd ai-service
pip install -r requirements.txt
pytest tests/ -v
```

Expected: **8 tests passed**

### Backend tests (JUnit 5)

```bash
cd backend
./mvnw test
```

Expected: **10+ tests passed, JaCoCo coverage ≥ 80%**

---

## Project Structure

```
tool-114/                          ← project root
│
├── ai-service/                    ← Flask AI microservice (port 5000)
│   ├── routes/
│   │   ├── describe.py            ← POST /describe
│   │   ├── recommend.py           ← POST /recommend
│   │   ├── report.py              ← POST /generate-report
│   │   └── health.py              ← GET /health
│   ├── services/
│   │   ├── groq_client.py         ← Groq API wrapper (3-retry + backoff)
│   │   ├── sanitiser.py           ← HTML strip + injection detection
│   │   ├── cache_service.py       ← Redis cache (SHA256, 15 min TTL)
│   │   └── chroma_service.py      ← ChromaDB + sentence-transformers
│   ├── prompts/
│   │   ├── describe_prompt.txt
│   │   ├── recommend_prompt.txt
│   │   └── report_prompt.txt
│   ├── tests/
│   │   └── test_ai_service.py     ← 8 pytest unit tests (Groq mocked)
│   ├── app.py                     ← Flask entry point
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── backend/                       ← Spring Boot backend (port 8080)
│   └── src/main/java/com/internship/tool/
│       ├── controller/            ← REST endpoints
│       ├── service/
│       │   └── AiServiceClient.java   ← calls Flask AI service
│       ├── repository/
│       ├── entity/
│       ├── config/
│       │   └── RestTemplateConfig.java
│       └── exception/
│
├── frontend/                      ← React 18 + Vite (port 80)
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── services/
│       └── App.jsx
│
├── docker-compose.yml             ← starts all 5 services
├── .env.example                   ← copy to .env and fill in values
├── .gitignore                     ← .env and build artifacts excluded
└── README.md
```

---

## Environment Variables Reference

| Variable           | Required | Default                    | Description                   |
|--------------------|----------|----------------------------|-------------------------------|
| `POSTGRES_PASSWORD`| ✅ Yes   | —                          | Database password             |
| `POSTGRES_USER`    | No       | `tool114user`              | Database username             |
| `POSTGRES_DB`      | No       | `tool114`                  | Database name                 |
| `JWT_SECRET`       | ✅ Yes   | —                          | Min 64 chars, random          |
| `JWT_EXPIRY_MS`    | No       | `86400000`                 | Token expiry (24h)            |
| `GROQ_API_KEY`     | ✅ Yes   | —                          | From console.groq.com         |
| `GROQ_MODEL`       | No       | `llama-3.3-70b-versatile`  | Groq model name               |
| `MAIL_USERNAME`    | ✅ Yes   | —                          | Gmail address                 |
| `MAIL_PASSWORD`    | ✅ Yes   | —                          | Gmail App Password            |
| `FLASK_ENV`        | No       | `production`               | Set `development` for debug   |

---

## Team

| Role            | Responsibilities                                              |
|-----------------|---------------------------------------------------------------|
| Java Developer 1 | Spring Boot, Service layer, JWT, Docker Compose, README     |
| Java Developer 2 | DB schema, Repository, React frontend, Email, demo video    |
| AI Developer 1  | Flask setup, prompts, /describe /recommend /health endpoints |
| AI Developer 2  | GroqClient, /generate-report, security review, prompt tuning |
| Security Reviewer | Security testing, SECURITY.md, Demo Day security segment  |

---

## Common Issues

**`docker-compose up` fails on first run**
Ensure `.env` exists and all `REQUIRED` values are filled. Run `docker-compose config` to validate.

**AI service shows `unhealthy`**
Check your `GROQ_API_KEY` is correct. Test it: `docker-compose logs ai-service`

**Port 80 already in use**
Stop any local web server (nginx, Apache) or change the frontend port in `docker-compose.yml`.

**Empty database on demo**
Run `docker-compose down -v && docker-compose up` — the data seeder runs automatically on startup.

---

*Tool-114 — Residual Risk Calculator | Capstone Project | Sprint: 14 April – 9 May 2026*
