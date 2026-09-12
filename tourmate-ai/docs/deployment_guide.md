# TourMate AI - Production Deployment Guide (Phase 14)

This guide provides end-to-end instructions for deploying TourMate AI to the cloud using **Vercel** (Frontend), **Render** (Backend), and **MongoDB Atlas** (Database).

---

## 1. Prerequisites Checklist
- [x] GitHub repository with latest codebase pushed (`https://github.com/mukesh941/tourmate.git`).
- [x] Free account on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
- [x] Free account on [Render](https://render.com).
- [x] Free account on [Vercel](https://vercel.com).

---

## 2. Step 1: Database Setup (MongoDB Atlas)

1. **Log in to MongoDB Atlas**:
   - Create a free **M0 Shared Cluster** (e.g., AWS / Frankfurt or Mumbai).
2. **Configure Database User**:
   - Under **Security > Database Access**, click **Add New Database User**.
   - Authentication method: `Password`.
   - Role: `Read and write to any database`.
   - Save the username and password securely.
3. **Configure Network Access (Crucial for Cloud Deployment)**:
   - Under **Security > Network Access**, click **Add IP Address**.
   - Select **Allow Access from Anywhere** (`0.0.0.0/0`).
   - *Reason:* Serverless clouds like Render and Vercel do not use static egress IP addresses.
4. **Get Connection String**:
   - Click **Connect > Drivers > Python (Motor/PyMongo)**.
   - Copy the URI:
     ```text
     mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
     ```

---

## 3. Step 2: Backend Deployment (Render)

### Option A: Using the Render Blueprint (`render.yaml`)
1. In the Render Dashboard, click **New > Blueprint**.
2. Connect your `tourmate` GitHub repository.
3. Render will detect `render.yaml` automatically.
4. Supply your secret environment variables when prompted (`MONGO_URI`, `CORS_ORIGINS`).

### Option B: Manual Web Service Setup
1. In Render, click **New > Web Service**.
2. Connect your GitHub repository.
3. Configure the following fields:
   - **Name**: `tourmate-backend`
   - **Region**: Oregon or Frankfurt
   - **Root Directory**: `tourmate-ai/backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
4. Add **Environment Variables**:
   | Variable | Value | Notes |
   |---|---|---|
   | `MONGO_URI` | `mongodb+srv://...` | From MongoDB Atlas |
   | `MONGO_DB_NAME` | `tourmate` | Database name |
   | `JWT_SECRET_KEY` | *(32+ char random string)* | Generates secure JWTs |
   | `JWT_ALGORITHM` | `HS256` | Default |
   | `CORS_ORIGINS` | `https://your-frontend.vercel.app` | Comma-separated |
   | `GEMINI_API_KEY` | *(optional)* | Google Gemini API Key |
5. Click **Create Web Service**.
6. Once deployed, note your service URL: e.g. `https://tourmate-backend.onrender.com`. Test health at `https://tourmate-backend.onrender.com/health`.

---

## 4. Step 3: Frontend Deployment (Vercel)

1. Log in to [Vercel](https://vercel.com) and click **Add New > Project**.
2. Import your `tourmate` repository.
3. Configure the project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click *Edit* and select `tourmate-ai/frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
4. Add **Environment Variables**:
   | Key | Value |
   |---|---|
   | `VITE_API_BASE_URL` | `https://tourmate-backend.onrender.com/api` |
5. Click **Deploy**.
6. Vercel automatically deploys the frontend with deep-linking SPA rewrites powered by `tourmate-ai/frontend/vercel.json`.

---

## 5. Step 4: Finalize CORS & Database Seeding

1. **Update Backend CORS**:
   - Go back to Render Dashboard > `tourmate-backend` > **Environment**.
   - Update `CORS_ORIGINS` to include your newly assigned Vercel URL (e.g. `https://tourmate-ai.vercel.app,http://localhost:5173`).
2. **Seed Initial Destination & Tourist Place Data**:
   - Run the seed script from your local machine targeting the Atlas cluster:
     ```powershell
     cd tourmate-ai/backend
     $env:MONGO_URI="mongodb+srv://<username>:<password>@<cluster>.mongodb.net"
     python seed_db.py
     ```
   - This populates destinations and places with **verified high-resolution real photography** (no AI art or placeholders).

---

## 6. Local Dockerized Deployment (Alternative)

To run the entire containerized production stack locally using Docker Compose:

```bash
cd tourmate-ai
docker-compose up --build
```

Services will start:
- **Frontend (Nginx SPA)**: `http://localhost:5173`
- **Backend (FastAPI)**: `http://localhost:8000`
- **MongoDB**: `localhost:27017`
