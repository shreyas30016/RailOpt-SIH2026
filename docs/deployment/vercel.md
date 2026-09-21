# Vercel Frontend Deployment Guide

## Overview
RailOpt's frontend is a modern static single-page application built with HTML5, vanilla JavaScript (ES modules), and Tailwind CSS. It is designed to deploy on the **Vercel Edge Network** with clean routing and zero serverless Python dependencies.

---

## Why Decoupled from Backend?
The RailOpt backend relies on **Google OR-Tools CP-SAT**, a heavy C++ mathematical solver with binary Python wheels exceeding ~100 MB compressed. Forcing OR-Tools into Vercel Serverless Functions causes package size rejections, cold-start latency, and CPU execution timeouts.

By deploying the frontend as static assets on Vercel and the FastAPI backend on an external container host (e.g. Render, Railway, Fly.io, AWS ECS), both tiers operate in their optimal runtime environments.

---

## Routing Configuration (`vercel.json`)
The repository includes a production-ready `vercel.json` file configuring SPA routing rewrites:

```json
{
  "version": 2,
  "cleanUrls": true,
  "trailingSlash": false,
  "rewrites": [
    { "source": "/static/(.*)", "destination": "/frontend/$1" },
    { "source": "/assets/(.*)", "destination": "/frontend/assets/$1" },
    { "source": "/js/(.*)", "destination": "/frontend/js/$1" },
    { "source": "/", "destination": "/frontend/login.html" },
    { "source": "/login", "destination": "/frontend/login.html" },
    { "source": "/dashboard", "destination": "/frontend/dashboard.html" },
    { "source": "/maintenance-requests", "destination": "/frontend/maintenance-requests.html" },
    { "source": "/block-planning", "destination": "/frontend/block-planning.html" },
    { "source": "/planning", "destination": "/frontend/block-planning.html" },
    { "source": "/gantt-view", "destination": "/frontend/gantt-view.html" },
    { "source": "/gantt", "destination": "/frontend/gantt-view.html" },
    { "source": "/what-if", "destination": "/frontend/what-if.html" },
    { "source": "/constraints-logic", "destination": "/frontend/constraints-logic.html" },
    { "source": "/reports", "destination": "/frontend/reports.html" }
  ]
}
```

---

## Deployment Steps

### 1. Import Project into Vercel
1. Log into your [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** → **Project**.
3. Select the `shreyas30016/Railopt-SIH2026` repository.

### 2. Configure Build & Output Settings
- **Framework Preset**: `Other`
- **Root Directory**: `./` (Default root)
- **Build Command**: *Leave blank* (No compile/bundle step needed)
- **Output Directory**: *Leave blank*
- **Install Command**: *Leave blank*

### 3. Deploy
Click **Deploy**. Vercel will immediately deploy the static assets to an edge URL (e.g. `https://railopt-sih2026.vercel.app`).

---

## Configuring Backend API URL on Deployed Frontend
The frontend determines the backend API URL dynamically via `frontend/js/config.js` following this priority order:

1. **Global Injection**: `window.__RAILOPT_CONFIG__.API_BASE_URL`
2. **HTML Meta Tag**: `<meta name="railopt-api-base" content="https://your-backend.onrender.com">` in `frontend/index.html`
3. **Browser Override**: `localStorage.setItem("railopt_api_base_url", "https://your-backend.onrender.com")`
4. **Relative Fallback**: `""` (used when backend is reverse-proxied or in local unified development)

To connect your deployed frontend to your deployed backend:
Open the browser developer console on your Vercel URL and run:
```javascript
localStorage.setItem("railopt_api_base_url", "https://your-fastapi-backend-url.com");
location.reload();
```
