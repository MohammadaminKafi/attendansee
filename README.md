# AttendanSee

Computer-vision attendance for classrooms. Upload photos, detect faces, generate embeddings, and cluster or assign face crops to students — then view per-session and per-class attendance.

## Architecture
- Backend: Django + DRF, PostgreSQL with `pgvector`, OpenCV/DeepFace, clustering/assignment services.
- Frontend: React + Vite + Nginx.
- Orchestration: Docker Compose (root). Media stored under `backend/media/` (mounted volume).

## Quick Start (Docker)
The whole project is served via the root compose file.
```bash
cp .env.docker .env
docker compose up -d --build
```
- UI: `http://localhost:53000`
- API: `http://localhost:58000/api`
- Swagger: `http://localhost:58000/swagger/`

Tip: set `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, `DJANGO_SUPERUSER_EMAIL` in `.env` to auto-create an admin user.

## Environment (.env.docker)
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `CORS_ALLOWED_ORIGINS`, `CORS_ALLOW_ALL_ORIGINS`
- `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, `DJANGO_SUPERUSER_EMAIL`
- `GUNICORN_WORKERS`, `GUNICORN_TIMEOUT`, `GUNICORN_GRACEFUL_TIMEOUT`

Frontend container reads `VITE_API_BASE_URL` from docker-compose and injects it at runtime.

## Core Workflow
1) Create a class, add students (CSV/Excel bulk supported).
2) Create a session and upload class images.
3) Process images to detect faces and create face crops.
4) Generate embeddings (ArcFace/FaceNet512).
5) Cluster crops or auto-assign via similarity; optionally review manually.
6) View attendance reports per session and across the class.

See `backend/README.md` for API examples and `frontend/README.md` for UI flows. Backend dev uses `uv`.

## Repo Layout
- `backend/`: Django + DRF services and APIs
- `frontend/`: React UI served by Nginx
- `docker-compose.yml`: full stack definition
