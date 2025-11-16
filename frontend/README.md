# Frontend (React + Vite)

UI for classes, sessions, images, face crops, and attendance reports. Handles login via JWT (Djoser) and calls the backend API.

## Dev Setup
### Prerequisites
- Node.js 18+

### Start Dev Server
```bash
cd frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000/api" > .env.local
npm run dev
```
- App: `http://localhost:3000`
- Set `VITE_API_BASE_URL` to your backend dev URL (default backend dev is 8000).

For integrated runs, use the root `docker-compose.yml` (serves Nginx on 53000 and backend on 58000).

## Runtime Config (Docker)
- The container reads `VITE_API_BASE_URL` from docker-compose and injects it at runtime via `docker-entrypoint.sh`.
- Default compose maps it to `http://localhost:58000/api`.

## Pages & Flows
- Login: JWT auth, then redirect to Classes.
- Classes: create/delete, stats, bulk student upload.
- Class Detail: sessions list, class-level tools (process images, generate embeddings, cluster, auto-assign, reports).
- Session Detail: upload images, process images, crops list (identified/unidentified), per-session reports.
- Image Detail: run face detection, view processed image, browse crops.
- Face Crop Detail: generate embedding, similar faces, auto-assign, assign-from-candidate, unidentify.
- Student Detail: per-student attendance.

