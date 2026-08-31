# Technical Audit: RailOpt Mathematical Optimization Engine (SIH26027)

This document provides a comprehensive technical audit of the Railway Maintenance Block Optimization Engine built with **Google OR-Tools CP-SAT** in [`backend/app/optimizer/solver.py`](file:///a:/SHREYAS/RAILWAY%20BLOCK%20AI/backend/app/optimizer/solver.py).

---

## 1. Decision Variables

For each maintenance job $j \in J$ (where $|J| = N$ jobs) and train $t \in T$:

| Variable | CP-SAT Type | Domain / Bounds | Mathematical Role |
|:---|:---|:---|:---|
| $\text{sched}_j$ | `BoolVar` | $\{0, 1\}$ | $1$ if job $j$ is admitted into the scheduled plan; $0$ if deferred. |
| $\text{start}_j$ | `IntVar` | $[\text{earliest}_j, \text{latest}_j - d_j]$ | Scheduled start minute of job $j$ (minutes from 00:00, $[0, 1440]$). |
| $\text{end}_j$ | `IntVar` | $[\text{earliest}_j + d_j, \text{latest}_j]$ | Scheduled end minute of job $j$, where $\text{end}_j = \text{start}_j + d_j$. |
| $\text{interval}_j$ | `OptionalIntervalVar` | $(\text{start}_j, d_j, \text{end}_j, \text{sched}_j)$ | Time interval active only if $\text{sched}_j = 1$. |
| $\text{shadow}_{j_1, j_2}$ | `BoolVar` | $\{0, 1\}$ | $1$ if compatible jobs $j_1, j_2$ form a synchronized multi-department shadow block. |
| $\text{delay}_t$ | `IntVar` | $[0, \text{max\_delay}_t]$ | Permitted regulation delay for train $t$ (0–25 min for Premium, 0–45 min for Express, 0–240 min for Freight). |
| $j_1\text{\_before\_}j_2$ | `BoolVar` | $\{0, 1\}$ | Disjunctive ordering indicator ($1 \implies \text{end}_{j_1} \le \text{start}_{j_2}$). |
| $t\text{\_before\_}j$ | `BoolVar` | $\{0, 1\}$ | Train passes through section before block start ($\text{exit}_{t,s} + 3 \le \text{start}_j$). |
| $t\text{\_after\_}j$ | `BoolVar` | $\{0, 1\}$ | Train passes after block release with delay ($\text{end}_j + 3 \le \text{entry}_{t,s} + \text{delay}_t$). |

---

## 2. Hard Constraints Currently Implemented

These constraints are non-negotiable physical and safety conditions; candidate plans violating any condition are discarded by the solver:

1. **Job Time Window Bounds**:
   $$\text{start}_j \ge \text{earliest}_j, \quad \text{end}_j \le \text{latest}_j \quad \forall j \in J$$
2. **Machine Resource Exclusivity**:
   For each specialized heavy machine $m \in M$ (e.g. `CSM 09-32`, `DTS-102`, `Tower Wagon TRD-01`, `USFD Unit`):
   $$\text{NoOverlap}(\{\text{interval}_j \mid \text{resource}(j) = m\})$$
3. **Track Line Disjunctive Non-Overlap (unless Shadow Block)**:
   For all pairs $(j_1, j_2)$ on the same track line $L$:
   $$(\text{end}_{j_1} \le \text{start}_{j_2}) \lor (\text{end}_{j_2} \le \text{start}_{j_1}) \lor \text{shadow}_{j_1, j_2} \lor \neg \text{sched}_{j_1} \lor \neg \text{sched}_{j_2}$$
4. **Shadow Block Start-Time Synchronization**:
   $$\text{shadow}_{j_1, j_2} \implies (\text{start}_{j_1} = \text{start}_{j_2} \land \text{sched}_{j_1} \land \text{sched}_{j_2})$$
5. **Train Timetable Safety & Corridor Headway**:
   On 2-track sections without a 3rd line, for each train $t$ sharing direction with traffic block job $j$:
   $$(\text{exit}_{t,s} + 3 \le \text{start}_j) \lor (\text{end}_j + 3 \le \text{entry}_{t,s} + \text{delay}_t) \lor \neg \text{sched}_j$$
6. **Maximum Permissible Train Regulation Delay**:
   $$\text{delay}_t \le \begin{cases} 25 \text{ min} & \text{if priority}(t) \ge 30 \text{ (Vande Bharat / Rajdhani)} \\ 45 \text{ min} & \text{if priority}(t) \ge 15 \text{ (Mail / Express)} \\ 240 \text{ min} & \text{if priority}(t) < 15 \text{ (Freight / Container)} \end{cases}$$

---

## 3. Soft Objectives Currently Optimized

1. **Maximizing Scheduled Maintenance Execution**: Prioritize critical and high-priority maintenance demand.
2. **Maximizing Multi-Department Shadow Block Synergy**: Heavily reward co-locating Civil Engineering, TRD, and S&T works during the same corridor possession.
3. **Minimizing Train Disruption & Passenger Delay**: Penalize train regulation delays proportionally to train priority.

---

## 4. Objective Weights & Scoring Formula

$$\text{Maximize } Z = \sum_{j \in J} W_j \cdot \text{sched}_j + \sum_{(j_1, j_2) \in S} B_{\text{shadow}} \cdot \text{shadow}_{j_1, j_2} - \sum_{t \in T} C_t \cdot \text{delay}_t$$

### Term Coefficients:

| Parameter | Symbol | Value | Rationale |
|:---|:---|:---|:---|
| **Job Execution Weight** | $W_j$ | $\text{priority}_j \times 2000 + U_j$ | $\text{priority}_j \in [1, 5]$. $U_{\text{CRITICAL}} = 3000$, $U_{\text{HIGH}} = 1500$, $U_{\text{ROUTINE}} = 800$. |
| **Shadow Synergy Bonus** | $B_{\text{shadow}}$ | $+4000$ | Rewards combining distinct department requests into one corridor closure. |
| **Vande Bharat / Rajdhani Delay Penalty** | $C_{\text{Premium}}$ | $50 / \text{min}$ | Extreme penalty to protect mission-critical punctuality index. |
| **Mail / Express Delay Penalty** | $C_{\text{Express}}$ | $20 / \text{min}$ | Standard passenger train regulation penalty. |
| **Freight Train Delay Penalty** | $C_{\text{Freight}}$ | $2 / \text{min}$ | Nominal penalty allowing freight holding in siding loops. |

---

## 5. How Train Conflicts Are Represented

1. **Section Transit Calculation**: The corridor is represented as an ordered sequence of 6 sections (`NDLS-TKD`, `TKD-FDB`, `FDB-PWL`, `PWL-KDS`, `KDS-MTJ`, `MTJ-AGC`). Train departure and arrival minutes define section entry minute $\text{entry}_{t,s}$ and exit minute $\text{exit}_{t,s}$.
2. **3rd Line Bypass Logic**: If a section has a dedicated 3rd line (`3RD_LINE`), traffic block jobs on main lines allow passenger trains to be routed via the 3rd line without creating a conflict.
3. **Disjunctive Deconfliction**: If no 3rd line exists, boolean flags $t\text{\_before\_}j$ and $t\text{\_after\_}j$ enforce that the train must clear the section with a safety buffer of at least 3 minutes before the block starts or after the block ends (absorbing $\text{delay}_t$).

---

## 6. How Maintenance Jobs Are Assigned to Blocks

- Each maintenance job $j$ defines duration $d_j$, section $s$, track line $l$, earliest start minute, and latest end minute.
- The solver chooses exact integer minutes $\text{start}_j$ and $\text{end}_j = \text{start}_j + d_j$ within approved lull windows.
- Each accepted job produces a `ScheduledBlock` record linking the job, section, track line, and start/end time.

---

## 7. How Job Dependencies Are Represented

- **Power Block Coupling**: If a Civil Engineering job requires traction shutdown (`requires_power_block = True`), it is paired with a Traction Distribution (TRD) OHE power isolation block.
- **Resource Constraints**: Jobs requiring the same tamping machine or tower wagon cannot overlap in time anywhere in the division (`model.AddNoOverlap`).

---

## 8. How Department Coordination & Shadow Blocks Are Represented

- Co-location compatibility function:
  $$\text{can\_form\_shadow\_block}(j_1, j_2) = (\text{section}_{j_1} = \text{section}_{j_2}) \land (\text{line}_{j_1} = \text{line}_{j_2}) \land (\text{dept}_{j_1} \ne \text{dept}_{j_2})$$
- When $\text{shadow}_{j_1, j_2} = 1$, the solver sets $\text{start}_{j_1} = \text{start}_{j_2}$, allowing both departments (e.g. Civil Track Tamping + TRD OHE Cantilever Adjustment) to work in the same track window simultaneously.

---

## 9. How Unscheduled Jobs Are Handled

- If total maintenance demand exceeds available track lull capacity, lower priority / routine jobs have $\text{sched}_j = 0$.
- Unscheduled jobs are extracted by comparing all active demands against scheduled block IDs.
- Each unscheduled job is tagged with:
  - Deferral reason (e.g. *"Deferred due to high passenger train traffic density during available window."*)
  - Suggested alternative (e.g. *"Reschedule to next day night window (01:30 - 05:30)."*)

---

## 10. How KPIs Are Calculated

1. **Scheduled Jobs Count**: $N_{\text{sched}} = \sum_{j \in J} \text{sched}_j$
2. **Total Maintenance Hours**: $H_{\text{maint}} = \frac{1}{60} \sum_{j \in J_{\text{sched}}} d_j$
3. **Total Train Delay Minutes**: $D_{\text{train}} = \sum_{t \in T} \text{delay}_t$
4. **Block Window Utilization %**: $U = \frac{\sum \text{Allocated Block Minutes}}{\sum \text{Available Window Minutes}} \times 100\%$
5. **Shadow Block Synergy %**: $S_{\text{pct}} = \frac{|\{j \in J_{\text{sched}} \mid \text{is\_shadow}(j) = \text{True}\}|}{N_{\text{sched}}} \times 100\%$

---

## 11. How What-If Replanning Modifies the Input Model

In [`backend/app/optimizer/whatif.py`](file:///a:/SHREYAS/RAILWAY%20BLOCK%20AI/backend/app/optimizer/whatif.py):
1. **Baseline Capture**: Solves the initial scenario and captures baseline KPIs ($N_0, H_0, D_0, U_0$).
2. **Disruption Injection**:
   - For an **Emergency Track Fracture / Urgent Work**: Injects a temporary `MaintenanceJob` with $\text{priority} = 5, \text{urgency} = \text{CRITICAL}$.
   - For a **Train Delay**: Injects forced train schedule offsets.
3. **Re-optimization**: Runs the CP-SAT solver over the combined model with safety constraints enforced.
4. **Delta Calculation**: Computes $\Delta N = N_1 - N_0$, $\Delta D = D_1 - D_0$, $\Delta U = U_1 - U_0$ and generates human-readable impact alerts.

---

## 12. Classification of Railway-Specific Rules

| Rule / Behavior | Implementation Source | Domain Validation Classification |
|:---|:---|:---|
| Disjunctive track non-overlap (single train/machine on track at a time) | `solver.py` Line 144 | **VALIDATED BY DOMAIN EXPERT** |
| Premium train protection (Vande Bharat / Rajdhani tight bounds) | `solver.py` Line 161 | **VALIDATED BY DOMAIN EXPERT** |
| Machine resource exclusivity (`AddNoOverlap`) | `solver.py` Line 108 | **VALIDATED BY DOMAIN EXPERT** |
| 3-minute safety headway buffer between block release and train entry | `solver.py` Line 195 | **PROTOTYPE ASSUMPTION** |
| Simultaneous track occupation between ENG and TRD in a Shadow Block | `constraints.py` Line 68 | **PROTOTYPE ASSUMPTION** |
| Freight trains holding up to 240 minutes in loop sidings | `solver.py` Line 166 | **PROTOTYPE ASSUMPTION** |
| Uniform transit time distribution across 6 sections | `solver.py` Line 179 | **UNKNOWN / NEEDS VALIDATION** |
| Turnout point machine testing concurrent with main-line block | `constraints.py` Line 69 | **UNKNOWN / NEEDS VALIDATION** |

---

## 13. Mathematical & Solver Summary

- **Solver Engine**: Google OR-Tools CP-SAT (Constraint Programming with SAT-based lazy clause generation).
- **Correctness**: The mathematical model strictly guarantees:
  1. No track line collisions occur.
  2. No heavy machines are double-booked.
  3. No passenger train delays exceed their hard upper limits.
  4. Optimality is mathematically proven ($\text{Status} = \text{OPTIMAL}$).
