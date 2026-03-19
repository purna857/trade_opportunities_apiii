# Trade Opportunities API

A FastAPI service that analyzes current Indian sector news and returns a structured markdown market analysis report.

## Features

- `GET /analyze/{sector}` main endpoint
- Session management using signed cookie sessions
- In-memory per-session usage tracking
- In-memory rate limiting
- API key authentication with optional guest mode for demos
- Gemini integration for sector analysis
- Current market/news collection using Google News RSS search for India-focused sector signals
- Graceful fallback markdown when AI is unavailable
- Automatic interactive docs at `/docs`

## Project Structure

```text
trade_opportunities_api/
├── app/
│   ├── core/
│   │   ├── auth.py
│   │   ├── rate_limit.py
│   │   └── store.py
│   ├── services/
│   │   ├── analysis.py
│   │   └── search.py
│   ├── config.py
│   ├── main.py
│   └── models.py
├── .env.example
├── README.md
└── requirements.txt
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate       # Windows PowerShell

pip install -r requirements.txt
cp .env.example .env
```

Update `.env` with your real values:

- `GEMINI_API_KEY`: from Google AI Studio
- `TRADE_API_KEY`: your private API key for requests
- `SESSION_SECRET_KEY`: long random secret for signed sessions

## Run

```bash
uvicorn app.main:app --reload
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

## Main Endpoint

### Request

```http
GET /analyze/pharmaceuticals
X-API-Key: change-me-in-production
```

If `GUEST_ACCESS_ENABLED=true`, the endpoint also works without the header for local demo purposes.

### Response

Returns `text/markdown`.

Example output structure:

```md
# Market Analysis Report: Pharmaceuticals
## Executive Summary
## Current Trade Opportunities
## Key Catalysts
## Risks and Headwinds
## What to Watch Next
## Source Snapshot
```

## Security Notes

- Input validation is enforced with Pydantic.
- Sessions are signed using `SessionMiddleware`.
- Rate limiting is applied per session/user in memory.
- API key auth is supported without adding extra endpoints.
- In production, disable guest access and use a strong secret.

## Error Handling

- `422` for invalid sector input
- `429` for rate limit violations
- `502` when external market data collection fails
- `500` for unexpected server-side errors

## Example curl

```bash
curl -H "X-API-Key: change-me-in-production" \
  http://127.0.0.1:8000/analyze/technology
```

## Notes

- Storage is intentionally in-memory only.
- Session stats and rate-limit counters reset when the process restarts.
- The report is informational and not investment advice.
