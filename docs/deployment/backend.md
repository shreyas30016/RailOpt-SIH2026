# FastAPI & OR-Tools Backend Deployment Guide

## Overview
The RailOpt backend is a high-performance Python application combining **FastAPI**, **Google OR-Tools CP-SAT**, **SQLAlchemy**, and an **NVIDIA NIM / DeepSeek AI Copilot**.

This guide covers deploying the backend to modern cloud container and app platforms such as **Render**, **Railway**, **Fly.io**, or **AWS ECS/EC2**.

---

## Recommended Platforms

| Platform | Best For | Setup Complexity | Free / Low-Cost Tier |
| :--- | :--- | :--- | :--- |
| **Render** | Production Web Service | Very Simple | Yes (Hobby tier) |
| **Railway** | Quick Continuous Deployments | Very Simple | Yes (Trial credit) |
| **Fly.io** | Low-latency edge containers | Moderate | Yes |
| **AWS ECS / App Runner** | Enterprise scalability | Advanced | AWS Free Tier |

---

## Deployment on Render

### 1. Create a New Web Service
1. In the [Render Dashboard](https://dashboard.render.com), click **New +** → **Web Service**.
2. Connect your GitHub repository `shreyas30016/Railopt-SIH2026`.

### 2. Configure Runtime Settings
- **Runtime**: `Python 3`
- **Build Command**:
  ```bash
  pip install --upgrade pip && pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
  ```

### 3. Add Environment Variables
| Key | Value | Description |
| :--- | :--- | :--- |
| `CORS_ORIGINS` | `https://your-vercel-domain.vercel.app,http://localhost:8000` | Allowed frontend origins (no trailing slash) |
| `DATABASE_URL` | `postgresql://user:pass@host:5432/railopt` | Managed PostgreSQL database connection string |
| `AI_PROVIDER` | `nvidia` | Model provider (`nvidia` or `mock`) |
| `AI_API_KEY` | `nvapi-...` | Your NVIDIA API key |
| `AI_MODEL` | `deepseek-ai/deepseek-v4-flash-0731` | Copilot model identifier |
| `TRAIN_DATA_PROVIDER` | `simulated` | `simulated` or `live` |

### 4. Health Check Endpoint
Render will verify your service via:
- **Path**: `/health`
- **Expected Status**: `200 OK`

---

## Deployment on Railway

1. In [Railway](https://railway.app), click **New Project** → **Deploy from GitHub repo**.
2. Select `shreyas30016/Railopt-SIH2026`.
3. Add a **PostgreSQL** database service within the Railway project canvas.
4. Connect the PostgreSQL `DATABASE_URL` variable to your Python web service.
5. Set `CORS_ORIGINS` to your Vercel URL.
6. Railway automatically detects `requirements.txt` and executes the start command.

---

## Production Database Note
- **Local / Demo Mode**: Defaults to SQLite (`railopt.db`).
- **Production Mode**: Supply a persistent PostgreSQL connection URI in `DATABASE_URL`. SQLAlchemy automatically provisions tables upon startup via `init_db()`.
- To seed the production database with the Delhi–Agra demo corridor, run:
  ```bash
  python scripts/seed_demo_data.py
  ```
