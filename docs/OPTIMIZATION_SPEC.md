# Complete Optimization Specification: RailOpt Solver Engine (SIH26027)

> **Source of Truth**: [`AGENTS.md`](file:///a:/SHREYAS/RAILWAY%20BLOCK%20AI/AGENTS.md)  
> **Core Principle**: *"AI predicts. Constraints protect. Optimization decides."*  
> **Solver Engine**: Google OR-Tools CP-SAT (`ortools.sat.python.cp_model`)

---

## 1. Decision Variables

The scheduling horizon is discretized into integer minute offsets within a 24-hour cycle: $t \in [0, 1440]$.

For each maintenance job demand $j \in J$ and train movement $t \in T$:

| Variable Symbol | CP-SAT Type | Mathematical Domain | Description / Physical Meaning |
|:---|:---|:---|:---|
| $\text{sched}_j$ | `BoolVar` | $\{0, 1\}$ | **Job Inclusion**: $1$ if job $j$ is admitted into the scheduled plan; $0$ if deferred to backlog. |
| $\text{start}_j$ | `IntVar` | $[\text{earliest}_j, \text{latest}_j - d_j]$ | **Start Minute**: Exact minute from 00:00 when maintenance possession begins on the track. |
| $\text{end}_j$ | `IntVar` | $[\text{earliest}_j + d_j, \text{latest}_j]$ | **End Minute**: Exact minute when track is handed back to operating controllers ($\text{end}_j = \text{start}_j + d_j$). |
| $\text{interval}_j$ | `OptionalIntervalVar` | $(\text{start}_j, d_j, \text{end}_j, \text{sched}_j)$ | **Track Possession Interval**: Active only when $\text{sched}_j = 1$; consumed by non-overlap and machine resource constraints. |
| $\text{shadow}_{j_1, j_2}$ | `BoolVar` | $\{0, 1\}$ | **Shadow Block Coupling**: $1$ if compatible jobs $j_1, j_2$ share the same track closure concurrently. |
| $\text{delay}_t$ | `IntVar` | $[0, \text{max\_delay}_t]$ | **Train Regulation**: Minutes of permitted siding hold or schedule shift for train $t$. |
| $j_1\text{\_before\_}j_2$ | `BoolVar` | $\{0, 1\}$ | **Disjunctive Track Precedence**: $1 \implies \text{end}_{j_1} \le \text{start}_{j_2}$. |
| $t\text{\_before\_}j$ | `BoolVar` | $\{0, 1\}$ | **Train Clearance Before Block**: $1 \implies \text{exit}_{t,s} + \text{buffer} \le \text{start}_j$. |
| $t\text{\_after\_}j$ | `BoolVar` | $\{0, 1\}$ | **Train Entry After Block**: $1 \implies \text{end}_j + \text{buffer} \le \text{entry}_{t,s} + \text{delay}_t$. |

---

## 2. What Makes a Maintenance Job Schedulable

A maintenance job demand $j$ is admitted into the plan ($\text{sched}_j = 1$) if and only if **all** of the following conditions hold simultaneously:
1. **Window Feasibility**: The job's duration $d_j$ fits within its allowable window:
   $$\text{earliest\_start}_j + d_j \le \text{latest\_end}_j$$
2. **Track Availability**: No other non-shadow job occupies the same track line during $[\text{start}_j, \text{end}_j]$.
3. **Machine Availability**: The requested heavy machinery (e.g. `CSM 09-32`, `Tower Wagon`) is not committed elsewhere during $[\text{start}_j, \text{end}_j]$.
4. **Train Punctuality Bounds**: Train regulation delays required to clear the block do not exceed maximum permissible limits (e.g. $\le 25\text{ min}$ for Vande Bharat).
5. **Precedence Prerequisite**: Any predecessor job on which job $j$ depends is also scheduled and completed before $\text{start}_j$.

---

## 3. How Train Movements Are Represented

- **Section Transit Path**: Each train $t$ has departure $\text{dep}_t$ and arrival $\text{arr}_t$. For each section $s \in \{0, 1, \dots, 5\}$ along the corridor:
  $$\text{entry}_{t,s} = \text{dep}_t + (s \times \Delta t_{\text{sec}}), \quad \text{exit}_{t,s} = \text{entry}_{t,s} + \Delta t_{\text{sec}}$$
- **3rd Line Bypass**: If a section possesses a dedicated 3rd line (`3RD_LINE`), traffic block jobs on main lines allow trains to be routed through the 3rd line without requiring train stoppage.
- **Disjunctive Deconfliction (2-Track Sections)**: When a traffic block is granted on a 2-track line sharing train direction:
  $$(\text{exit}_{t,s} + 3 \le \text{start}_j) \lor (\text{end}_j + 3 \le \text{entry}_{t,s} + \text{delay}_t) \lor (\text{sched}_j = 0)$$

---

## 4. How Block Windows Are Represented

- Block windows $W_k$ represent corridor lull periods officially agreed upon between Operating and Maintenance departments (e.g. night maintenance window $01:30\text{--}05:30$).
- Defined by: `section_id`, `track_line_id`, `start_minute`, `end_minute`, and `window_type` (`CORRIDOR`, `SHADOW`, `EMERGENCY`).
- The optimizer restricts job starts and completions inside these windows via variable domains.

---

## 5. How Resource Conflicts Are Handled

- Specialized heavy machines (Tamping machines `CSM 09-32`, Dynamic Track Stabilizers `DTS-102`, OHE Tower Wagons `TW-01`, Ultrasonic Rail Flaw Detectors `USFD`) are single-operator exclusive assets across the division.
- Handled via CP-SAT cumulative non-overlap constraints:
  $$\text{NoOverlap}(\{\text{interval}_j \mid \text{resource}(j) = m\})$$
- Guarantees zero double-booking across different corridor sections.

---

## 6. How Job Dependencies (Precedence) Are Handled

- When Job B (*e.g. Dynamic Track Stabilization*) depends on Job A (*e.g. Ballast Deep Screening*):
  1. **Inclusion Implication**: $\text{sched}_B \implies \text{sched}_A$ (If Job A cannot be scheduled, Job B is automatically rejected).
  2. **Temporal Precedence**:
     $$\text{end}_A \le \text{start}_B \quad \text{enforced when } \text{sched}_A \land \text{sched}_B$$

---

## 7. How Department Coordination & Shadow Blocks Are Handled

- **Co-Location Definition**: When two or more distinct departments (e.g. Civil Engineering track gang + TRD OHE wire adjustment gang) require possession of the **same section** and **same track line**:
- **Compatibility Matrix**: Loaded dynamically from [`constraints.py`](file:///a:/SHREYAS/RAILWAY%20BLOCK%20AI/backend/app/optimizer/constraints.py):
  - `ENG + TRD`: **Compatible** (*Shadow Block allowed*)
  - `ENG + S_T`: **Compatible** (*Shadow Block allowed*)
  - `TRD + S_T`: **Compatible** (*Shadow Block allowed*)
  - `ENG + ENG`: **Incompatible** (*Cannot shadow; sequential separation required*)
- **Start Time Synchronization**: When $\text{shadow}_{j_1, j_2} = 1$:
  $$\text{start}_{j_1} = \text{start}_{j_2}$$

---

## 8. Current Hard Constraints

| Constraint Name | Mathematical Formula | Enforced Action on Violation |
|:---|:---|:---|
| **Track Disjunctive Non-Overlap** | $\text{end}_{j_1} \le \text{start}_{j_2} \lor \text{end}_{j_2} \le \text{start}_{j_1} \lor \text{shadow}_{j_1, j_2} \lor \neg \text{sched}_{j_1} \lor \neg \text{sched}_{j_2}$ | Reject candidate schedule |
| **Machine Exclusivity** | $\text{NoOverlap}(\{\text{interval}_j \mid \text{resource}(j) = m\})$ | Reject candidate schedule |
| **Job Window Boundary** | $\text{start}_j \ge \text{earliest}_j \land \text{end}_j \le \text{latest}_j$ | Reject candidate schedule |
| **Job Precedence** | $\text{end}_{\text{pred}} \le \text{start}_{\text{dep}} \land (\text{sched}_{\text{dep}} \implies \text{sched}_{\text{pred}})$ | Reject candidate schedule |
| **Train Headway Clearance** | $(\text{exit}_{t,s} + 3 \le \text{start}_j) \lor (\text{end}_j + 3 \le \text{entry}_{t,s} + \text{delay}_t) \lor \neg \text{sched}_j$ | Reject candidate schedule |
| **Max Permissible Delay** | $\text{delay}_t \le \text{max\_delay}_t$ | Reject candidate schedule |

---

## 9. Current Soft Constraints

1. **Maximal Maintenance Completion**: Schedule as many high-priority and critical demands as possible.
2. **Shadow Block Synergy Maximization**: Prefer bundling multiple departmental works into shared windows over separate possessions.
3. **Passenger Disruption Minimization**: Schedule blocks during natural timetable lulls to keep passenger train delays at $0\text{ min}$.

---

## 10. Objective Function

$$\text{Maximize } Z = \sum_{j \in J} W_j \cdot \text{sched}_j + \sum_{(j_1, j_2) \in S} B_{\text{shadow}} \cdot \text{shadow}_{j_1, j_2} - \sum_{t \in T} C_t \cdot \text{delay}_t$$

---

## 11. Numerical Weights Currently Used

| Term | Parameter | Weight Value | Description / Operational Basis |
|:---|:---|:---|:---|
| **Job Base Priority** | $P_j$ | $\text{priority}_j \times 2000$ | Priority scale $1\text{--}5$. Critical P5 yields $10,000\text{ pts}$. |
| **Urgency Bonus: CRITICAL** | $U_{\text{CRITICAL}}$ | $+3000$ | Extra reward for emergency/critical track defects. |
| **Urgency Bonus: HIGH** | $U_{\text{HIGH}}$ | $+1500$ | Extra reward for overdue routine maintenance. |
| **Urgency Bonus: ROUTINE** | $U_{\text{ROUTINE}}$ | $+800$ | Standard planned maintenance reward. |
| **Shadow Synergy Bonus** | $B_{\text{shadow}}$ | $+4000$ | Large bonus for combining distinct departments into one block. |
| **Delay Penalty: Vande Bharat / Rajdhani** | $C_{\text{Premium}}$ | $-50 / \text{min}$ | Heavy penalty to prevent passenger express regulation. |
| **Delay Penalty: Mail / Express** | $C_{\text{Express}}$ | $-20 / \text{min}$ | Standard passenger regulation penalty. |
| **Delay Penalty: Freight / Goods** | $C_{\text{Freight}}$ | $-2 / \text{min}$ | Nominal penalty allowing freight holding in siding loops. |

---

## 12. What-If Replanning Logic

When an operational incident occurs (train delayed, emergency track fracture, block window cancelled):
1. **Baseline Freeze**: Solves baseline model and logs initial KPIs ($N_0, H_0, D_0, U_0$).
2. **Disruption Injection**: Modifies constraints or adds an emergency job with $\text{priority} = 5, \text{urgency} = \text{CRITICAL}$.
3. **Re-Optimization**: CP-SAT recalculates the schedule with hard safety constraints active.
4. **Delta Audit**: Computes $\Delta N, \Delta D, \Delta U$ and generates human-readable decision alerts explaining displaced or deferred jobs.

---

## 13. How KPI Values Are Calculated

1. **Scheduled Jobs Count**: $N_{\text{sched}} = \sum_{j \in J} \text{sched}_j$
2. **Total Maintenance Hours**: $H_{\text{maint}} = \frac{1}{60} \sum_{j \in J_{\text{sched}}} d_j$
3. **Total Train Delay Minutes**: $D_{\text{train}} = \sum_{t \in T} \text{delay}_t$
4. **Corridor Block Utilization %**: $U = \frac{\sum \text{Allocated Block Minutes}}{\sum \text{Available Window Minutes}} \times 100\%$
5. **Shadow Block Synergy %**: $S_{\text{pct}} = \frac{|\{j \in J_{\text{sched}} \mid \text{is\_shadow}(j) = \text{True}\}|}{N_{\text{sched}}} \times 100\%$

---

## 14. Classification of Domain Rules

| Rule Name | Code Reference | Classification |
|:---|:---|:---|
| **Disjunctive Track Line Non-Overlap** | `solver.py:144` | **VALIDATED BY DOMAIN EXPERT** |
| **Premium Passenger Train Protection** | `solver.py:161` | **VALIDATED BY DOMAIN EXPERT** |
| **Machine Resource Exclusivity (`AddNoOverlap`)** | `solver.py:108` | **VALIDATED BY DOMAIN EXPERT** |
| **3-Minute Safety Headway Margin** | `solver.py:195` | **PROTOTYPE ASSUMPTION** |
| **Shadow Block Co-Location Start Synchronization** | `solver.py:131` | **PROTOTYPE ASSUMPTION** |
| **Freight Train Loop Siding Holding Limit (240 min)** | `solver.py:166` | **PROTOTYPE ASSUMPTION** |
| **Uniform Train Transit Time Across 6 Sections** | `solver.py:179` | **UNKNOWN / NEEDS VALIDATION** |
| **Electronic Interlocking Testing Isolation Boundary** | `constraints.py:68` | **UNKNOWN / NEEDS VALIDATION** |

---

## 15. Worked Step-by-Step Example

### Step 1: Inputs
- **Section**: `NDLS-TKD` (`UP_MAIN` line).
- **Available Lull Window**: $01:30\text{--}04:30$ ($[90, 270]$, duration $180\text{ min}$).
- **Maintenance Demand**:
  1. `JOB-ENG-01`: Track Tamping ($d = 120\text{ min}$, Priority 5 Critical, requires `CSM-09`).
  2. `JOB-TRD-01`: OHE Cantilever Adjustment ($d = 120\text{ min}$, Priority 4 High).
  3. `JOB-SNT-01`: Axle Counter Testing ($d = 120\text{ min}$, Priority 2 Routine).
- **Train Movement**:
  - `Train 22436` (Vande Bharat): Departs 06:00 ($360\text{ min}$).
  - `Train BOXN-1` (Freight): Transit at 02:00 ($120\text{ min}$).

---

### Step 2: Constraints Formulation
1. **Window Boundary**: $\text{start}_j \ge 90 \land \text{start}_j + 120 \le 270 \implies \text{start}_j \in [90, 150]$.
2. **Shadow Block Compatibility**: `JOB-ENG-01` and `JOB-TRD-01` have different departments on the same track $\implies \text{can\_form\_shadow\_block} = \text{True}$.
3. **Sequential Separation**: `JOB-SNT-01` cannot shadow with another job from the same department or if window is full. Sequential time needed: $120 + 120 = 240\text{ min} > 180\text{ min}$ $\implies$ `JOB-SNT-01` must be deferred.
4. **Train Deconfliction**: Freight train held by $30\text{ min}$ in siding. Vande Bharat unaffected at 06:00 ($360 > 270$).

---

### Step 3: Optimization Objective Evaluation
- **Option A (Sequential, 1 Job Scheduled)**:
  $$Z = (5 \times 2000 + 3000) = 13,000$$
- **Option B (Shadow Block: ENG + TRD Bundled at 01:30)**:
  $$Z = (5 \times 2000 + 3000) + (4 \times 2000 + 1500) + 4000\text{ (Shadow Bonus)} - (2 \times 30\text{ Freight delay}) = 26,440$$

---

### Step 4: Solver Output
- **Solver Status**: `OPTIMAL`
- **Scheduled Blocks**:
  - `JOB-ENG-01`: Scheduled $01:30\text{--}03:30$ (`UP_MAIN`, `CSM-09` allocated).
  - `JOB-TRD-01`: Scheduled $01:30\text{--}03:30$ (`UP_MAIN`, co-located in Shadow Block with `JOB-ENG-01`).
- **Unscheduled / Deferred**:
  - `JOB-SNT-01`: Deferred (*"Corridor capacity full; rescheduled to next night window"*).
- **Resulting KPIs**:
  - Scheduled Jobs: $2 / 3$ ($66.7\%$)
  - Maintenance Hours: $4.0\text{ hrs}$
  - Passenger Train Delay: $0\text{ min}$
  - Shadow Block Synergy: $100.0\%$
  - Solver Time: $0.018\text{s}$
