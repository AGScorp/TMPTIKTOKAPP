# Holover App

Production-ready FastAPI backend integrating TikTok APIs (Login Kit, Content Posting, Display) with Postgres storage and Docker-based local development.

Key modules:
- FastAPI app [app/main.py](app/main.py:1)
- Config [app/core/config.py](app/core/config.py:1)
- Logging [app/core/logging.py](app/core/logging.py:1)
- Security/Crypto utils [app/core/security.py](app/core/security.py:1)
- DB session and models [app/db/session.py](app/db/session.py:1), [app/db/models.py](app/db/models.py:1)
- TikTok client [app/integrations/tiktok_client.py](app/integrations/tiktok_client.py:1) over HTTP layer [app/integrations/http.py](app/integrations/http.py:1)
- Routers: Auth [app/routers/auth.py](app/routers/auth.py:1), Content [app/routers/content.py](app/routers/content.py:1), Display [app/routers/display.py](app/routers/display.py:1)
- Services: OAuth [app/services/oauth.py](app/services/oauth.py:1), Tokens [app/services/tokens.py](app/services/tokens.py:1), Content [app/services/content.py](app/services/content.py:1), Display [app/services/display.py](app/services/display.py:1)
- Middleware [app/middleware/errors.py](app/middleware/errors.py:1), [app/middleware/observability.py](app/middleware/observability.py:1)

## Quickstart (Docker)
1. Copy .env.example to .env and fill values.
2. docker compose up --build
3. Visit http://localhost:8000/docs

