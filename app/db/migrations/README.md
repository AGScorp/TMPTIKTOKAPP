Alembic migrations for Holover App

Commands (run from repo root, ensure virtualenv is active and DATABASE_URL is set in .env):

1) Autogenerate initial migration from models:
   alembic -c alembic.ini revision --autogenerate -m "init schema"

2) Apply migrations:
   alembic -c alembic.ini upgrade head

3) Generate subsequent revisions on model changes:
   alembic -c alembic.ini revision --autogenerate -m "describe change"

Notes:
- The URL is sourced from .env via app settings; you can also override with env var:
  DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/holover
- Target metadata is app.db.models.Base
