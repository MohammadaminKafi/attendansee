# Backend (Django)

APIs and services for face detection, embeddings, clustering/assignment, and attendance.

## Stack
- Django + DRF, PostgreSQL (+ `pgvector`)
- OpenCV, DeepFace, scikit-learn, TensorFlow Keras
- Package management: `uv` (workspace at repo root)

## Capabilities
- Classes, students, sessions, images, and face crops (with 512D embeddings).
- Face detection (DeepFace backends: opencv, mtcnn, retinaface, mediapipe, yolov8, yunet, …).
- Embedding models: `arcface`, `facenet512`.
- Clustering (agglomerative cosine) and similarity-based auto-assign (KNN) with pgvector.
- Reports: per-session and per-class attendance matrices and statistics.

## Development (uv)
Run commands from repo root or `backend/` using `uv`.

1) Install `uv` (one-time):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2) Sync dependencies:
```bash
uv sync
```

3) Provide a DB and env
- Set `DB_*` vars (reuse `.env.docker` values) and `DEBUG=True`.
- Create the database and run migrations.

4) Common commands
```bash
# from backend/
uv run python manage.py migrate
uv run python manage.py runserver 0.0.0.0:8000

# tests
uv run pytest -q
```

Notes
- Serve the full stack via root `docker-compose.yml` for integrated runs.

## Environment
Key vars (see `.env.docker`):
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `CORS_ALLOWED_ORIGINS`, `CORS_ALLOW_ALL_ORIGINS`
- Optional: `DJANGO_SUPERUSER_*` to bootstrap an admin

## API Overview
- Auth (Djoser JWT): `/api/auth/`
	- `POST /auth/jwt/create/` (login), `POST /auth/jwt/refresh/`, `GET /auth/users/me/`
- Attendance: `/api/attendance/`
	- Classes CRUD: `/classes/`
	- Class tools: `/{id}/bulk-upload-students/`, `/{id}/statistics/`, `/{id}/attendance-report/`,
		`/{id}/process-all-images/`, `/{id}/generate-embeddings/`, `/{id}/cluster-crops/`,
		`/{id}/auto-assign-all-crops/`, `/{id}/suggest-assignments/`
	- Sessions CRUD: `/sessions/` with `/{id}/face-crops/`, `/{id}/generate-embeddings/`, `/{id}/cluster-crops/`, `/{id}/auto-assign-all-crops/`, `/{id}/suggest-assignments/`
	- Images CRUD+upload: `/images/` (+ `/{id}/process-image/`, `/{id}/face_crops/`)
	- Face crops: `/face-crops/` (+ `/{id}/generate-embedding/`, `/{id}/similar-faces/`, `/{id}/assign/`, `/{id}/assign-from-candidate/`, `/{id}/unidentify/`)

Swagger UI: `/swagger/`
