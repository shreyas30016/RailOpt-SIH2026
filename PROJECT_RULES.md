# SIH26027 Railway Block Planning — Project Rules & Governance

**One-Sentence Product Definition:**
> *"A railway-aware decision-support system that combines maintenance demand, train movements, and validated operational constraints to generate, explain, and dynamically replan efficient maintenance block schedules."*

---

## 1. Project Goal
Build a professional prototype for SIH 2026 Problem Statement **SIH26027 — AI-Powered Automatic Block Planning to Maximize Asset Availability for Train Operations on Indian Railways**.
- **Product Category**: Railway maintenance decision-support and optimization system.
- **Departments Coordinated**: Civil Engineering (Permanent Way), Traction Distribution (TRD / OHE), and Signal & Telecommunication (S&T).
- **Core Chain**:
  $$\text{Maintenance Demand} + \text{Train / Operating Windows} + \text{Validated Railway Constraints}$$
  $$\downarrow$$
  $$\text{Feasible Plans} \rightarrow \text{Optimized Block Plan} \rightarrow \text{Explainable Recommendation} \rightarrow \text{Human Review} \rightarrow \text{Dynamic Replanning}$$

---

## 2. Source of Truth & Data Honesty
- Official Scope based on SIH26027 description (BDMS, TMS/SMMS/TDMS, COA, train timetable, goods-train forecast, weekly/monthly planning).
- **Labels Required on All Data & Rules**:
  - Synthetic Data $\rightarrow$ `"Synthetic Demo Data"`
  - Live Train Data $\rightarrow$ `"Live/Public Train Data"`
  - Unvalidated Constraints $\rightarrow$ `"Prototype Constraint — Pending Domain Validation"`
- Never claim direct integration with internal Indian Railways systems (TMS, SMMS, TDMS, COA, BDMS, NTES) unless authorized credentials/access are provided.

---

## 3. Core Feature Hierarchy

### P0 — Must Work (Rock Solid)
1. Maintenance request management (ENG, TRD, S&T, MECH).
2. Train movement & operating window representation.
3. Railway constraint engine (Hard Safety vs Soft Optimization).
4. Maintenance priority & urgency handling.
5. Feasible block-plan generation via deterministic solver (Google OR-Tools CP-SAT).
6. Optimization of the feasible plan.
7. Gantt timeline visualization.
8. Before-vs-after KPIs.
9. Plan explanation (*"Why was this block chosen? Why was that deferred?"*).

### P1 — High-Value Differentiation
1. Multi-department job compatibility / Shadow Block bundling (ENG + TRD + S&T).
2. Dynamic replanning on live events (Train delayed, block extended, emergency work inserted).
3. What-if scenario simulation.
4. Human-in-the-loop lock / edit / recalculate.
5. Monthly $\rightarrow$ weekly $\rightarrow$ daily planning hierarchy.

### P2 — Optional / Future
1. Live/public train status adapter (already added with mock fallback).
2. ML prediction for duration/risk/traffic where justified (*"AI predicts. Constraints protect. Optimization decides."*).
3. Additional corridor scenarios (e.g. suburban).

---

## 4. Hard Constraints vs. Soft Objectives

| Constraint Type | Definition | Action on Violation | Example Mathematical / Operational Formulation |
|:---|:---|:---|:---|
| **HARD Safety Constraints** | Non-negotiable physical, safety, resource, and power isolation boundaries | **Reject candidate plan** | Track occupancy exclusivity ($j_1 \cap j_2 = \emptyset$ unless shadow-paired); OHE power shutdown synchronization; machine resource exclusivity. |
| **SOFT Optimization Objectives** | Operational preferences and efficiency bonuses | **Penalize / Reward objective function** | Minimize train delay minutes; maximize shadow block synergy; prioritize critical backlog; minimize corridor idle time. |

---

## 5. Architecture & Technology Stack

```
   ┌────────────────────────────────────────────────────────┐
   │             Presentation Layer (Stitch UI)              │
   │   Operations Dashboard | Maintenance | Block Planning   │
   │   Gantt Timeline | What-if Replanning | Plan Logic     │
   └───────────────────────────▲────────────────────────────┘
                               │ (Clean DOM & Component Library)
   ┌───────────────────────────┴────────────────────────────┐
   │                Data & Service Abstraction              │
   │    dataService.js | trainDataService.js (Mock/Live)    │
   └───────────────────────────▲────────────────────────────┘
                               │ REST APIs (FastAPI)
   ┌───────────────────────────┴────────────────────────────┐
   │             Deterministic Optimization Engine          │
   │   Google OR-Tools CP-SAT | Hard Constraints Engine     │
   │   Decision Explainer Tree | Dynamic Replanner          │
   └────────────────────────────────────────────────────────┘
```

---

## 6. 3-Minute Wednesday Selection Demo Flow

1. **Dashboard**: Show maintenance demand from ENG, TRD, and S&T alongside live corridor status.
2. **Maintenance Demands & Constraints**: Review priority backlog and safety constraints (*Pending Domain Validation*).
3. **Generate Plan**: Execute deterministic CP-SAT optimizer ($<1.5\text{s}$) $\rightarrow$ View Gantt timeline with multi-department shadow blocks.
4. **Explain Decision**: Click scheduled block $\rightarrow$ View *"Why this plan?"* mathematical reasoning tree.
5. **Trigger Live Event**: Inject train delay ($+20\text{ min}$) or emergency track fracture.
6. **Auto Replan**: View instant Before $\rightarrow$ After KPI delta, revised block timings, and conflict resolution audit.

---

## 7. Open Domain Questions (Pending Railway Validation)
- Exact combination rules for track machines (CSM tamping vs BCM screening vs Tower Wagon).
- Safety buffer times between block release and first train entry.
- Emergency track block preemption rules over scheduled passenger trains.
- Actual departmental approval workflows between Sr.DEN, Sr.DEE(TRD), and Sr.DSTE.
