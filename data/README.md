# Demo Corridor Data & Simulation Specifications

> **DISCLAIMER: SIMULATED / DEMO DATA**  
> All corridor layouts, station names, track line identifiers, train schedules, passenger train names, and maintenance job backlogs in this dataset are **synthetic demo artifacts** modeled after Indian Railways operational patterns. They do not represent real-time internal railway data from Indian Railways, NTES, or COA systems.

---

## Simulated Corridor: Delhi–Agra Section

The demo dataset simulates a representative high-density mixed passenger and freight corridor:

### Corridor Infrastructure
- **Sections (6)**:
  - `NDLS-NZM` (New Delhi - Hazrat Nizamuddin)
  - `NZM-FDB` (Hazrat Nizamuddin - Faridabad)
  - `FDB-PWL` (Faridabad - Palwal)
  - `PWL-KSV` (Palwal - Kosi Kalan)
  - `KSV-MTJ` (Kosi Kalan - Mathura Junction)
  - `MTJ-AGC` (Mathura Junction - Agra Cantt)
- **Track Lines (12)**: UP Main Line and DN Main Line for each corridor section.
- **Block Windows**: Configured maintenance windows per section and track line.

### Traffic Movements
- **Fleet (30 Trains)**:
  - High-priority Rajdhani, Shatabdi, and Vande Bharat Express services.
  - Superfast and Mail/Express passenger trains.
  - Container and bulk freight train paths.
- **Timetable Replay**: Moves trains realistically along the corridor according to IST wall clock time, calculating real-time KM positions and delays.

### Maintenance Backlog
- **Departments (3)**:
  - **ENG (Engineering / Civil)**: Track tamping, ballast screening, rail renewal.
  - **TRD (Traction Distribution / Electrical)**: OHE wire inspection, cantilever replacement.
  - **S&T (Signalling & Telecom)**: Point machine overhauls, track circuit testing.
- **Shadow Block Synergies**: Opportunities where TRD or S&T work can be executed safely within an Engineering traffic block on the same line, saving corridor capacity.

---

## Re-seeding the Database
To reset or re-seed the SQLite or PostgreSQL database with this clean baseline demo corridor:
```bash
python scripts/seed_demo_data.py
```
Or directly via the Python module:
```bash
python -m backend.app.data.synthetic_seeder
```
