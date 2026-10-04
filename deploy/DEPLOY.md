# Deployment Guide: Render & Vercel

Follow these steps to deploy your application.

## 1. Database (Neon Postgres)
- Create a project on [Neon.tech](https://neon.tech/).
- Copy your **Connection String**.
- **Important:** Rotate your password if you shared it in chat.

## 2. Backend (Render.com)
1. **New Web Service:** Point to this GitHub repo.
2. **Build Command:** `pip install --upgrade pip && pip install -r backend/requirements.txt`
3. **Start Command (API):** `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000`
4. **Environment Variables (API):**
   - `ENV=production`
   - `DATABASE_URL=<your-neon-connection-string>`
   - `INITIAL_USER=<unique_admin>`
   - `INITIAL_PASSWORD=<generated_secure_password>`
   - `META_ACCESS_TOKEN=<your_token>`
   - `IG_BUSINESS_ACCOUNT_ID=<your_id>`
   - `CORS_ORIGINS=["https://your-frontend-domain.vercel.app"]`
   - `RUN_WORKER=false` (If separating worker) or `true` (if combined)

## 3. Frontend (Vercel)
1. **Import:** Import the `/frontend` directory.
2. **Build Command:** `npm run build`
3. **Output Directory:** `dist`
4. **Environment Variable:**
   - `VITE_API_BASE_URL=https://your-render-app-url.onrender.com`

---
## Scaling for 1,000+ Users
When you reach higher load, create a SECOND Render service with:
- **Start Command:** `uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000`
- **Env:** `RUN_WORKER=true`, all other secrets the same.
- **API Service:** Set `RUN_WORKER=false`.
