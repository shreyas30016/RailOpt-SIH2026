"""
RailOpt Demo Data Seeder CLI
Seeds or resets the SQLite/PostgreSQL database with realistic synthetic corridor data
(Delhi - Agra corridor: 6 sections, 12 track lines, 30 trains, maintenance requests).
"""

import sys
from pathlib import Path

# Ensure repo root is in python path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.app.database import SessionLocal, Base, engine
from backend.app.data.synthetic_seeder import seed_synthetic_data


def main():
    print("==================================================================")
    print("  RailOpt (SIH 2026) — Synthetic Demo Corridor Data Seeder")
    print("==================================================================")
    print("[*] Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print("[*] Seeding demo corridor data (Delhi-Agra)...")
        seed_synthetic_data(db)
        print("[+] Demo data successfully populated!")
    except Exception as e:
        print(f"[!] Seeding error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
