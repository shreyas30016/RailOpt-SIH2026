# Local Development Setup

## Prerequisites
- **Python**: Version 3.10, 3.11, or 3.12 (Python 3.14 compatible).
- **Git**: For version control.
- **Web Browser**: Any modern browser (Chrome, Firefox, Edge).

---

## Quick Start (Windows)

The simplest way to start the complete system locally is to double-click [`run.bat`](file:///a:/SHREYAS/RAILWAY%20BLOCK%20AI/run.bat) at the repository root.

The script will:
1. Detect or activate the Python virtual environment (`.venv`).
2. Launch the FastAPI server at `http://127.0.0.1:8000`.
3. Open your default web browser directly to `http://127.0.0.1:8000/login`.

---

## Manual Setup (Cross-Platform / Linux / macOS)

### 1. Clone the Repository
```bash
git clone https://github.com/shreyas30016/Railopt-SIH2026.git
cd Railopt-SIH2026
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On Linux / macOS:
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment
Copy the template configuration file:
```bash
cp .env.example .env
```
*(Optional: add your `AI_API_KEY` in `.env` if testing NVIDIA DeepSeek Copilot)*

### 5. Seed the Demo Database
```bash
python scripts/seed_demo_data.py
```

### 6. Start the Server
```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 7. Access the Application
- **Web Interface**: [http://127.0.0.1:8000/login](http://127.0.0.1:8000/login)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
