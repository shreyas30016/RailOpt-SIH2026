# AI Architecture — RailOpt Railway Planning Copilot

**Sprint**: AI-FOUNDATION  
**Status**: Architecture complete. Live LLM integration intentionally NOT enabled.  
**Provider**: NVIDIA NIM (connect tomorrow — see §8)

---

## 1. Role of AI in RailOpt

The RailOpt AI Copilot is an **interpreter and orchestrator** only.

| Layer | Role |
| :--- | :--- |
| **AI Copilot** | Natural language interface — maps queries to backend tool calls |
| **RailOpt Backend** | Source of truth for all data and authorization |
| **OR-Tools CP-SAT** | Computation engine — all mathematical work |
| **Railway Constraints** | Safety authority — hard invariants, never negotiable |
| **Human Operator** | Final decision maker — AI supports, never replaces |

The AI must never invent data, claim feasibility without backend validation, or become a privilege escalation path.

---

## 2. Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│  Browser / Chat UI (future)                                  │
│  POST /api/ai/chat   GET /api/ai/status                      │
└──────────────────────┬───────────────────────────────────────┘
                       │ authenticated (same railopt_token)
┌──────────────────────▼───────────────────────────────────────┐
│  backend/app/api/ai_chat.py  (FastAPI router)                │
│  - Validates session via existing get_current_user()         │
│  - Instantiates AIOrchestrator with (provider, db, user)     │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│  backend/app/ai/orchestrator.py — AIOrchestrator             │
│  1. IntentClassifier.classify(message)                       │
│  2. Select tool from RailOptToolRegistry                     │
│  3. RBAC pre-check (current_user permissions)                │
│  4. ToolSpec.execute(args, db)        ───► Existing APIs     │
│  5. AIProvider.generate(result)                              │
│  6. Return ChatResponse                                      │
└──────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
 backend/app/ai/        backend/app/ai/     backend/app/ai/
   intent.py              tools.py            provider.py
 IntentClassifier     RailOptToolRegistry    AIProvider ABC
                                            MockAIProvider (now)
                                            NvidiaProvider (tomorrow)
         │
         ▼
  EXISTING BACKEND SERVICES (UNCHANGED)
  /api/dashboard  /api/maintenance  /api/optimization
  /api/gantt      /api/whatif       /api/reports
  DecisionExplainer  WhatIfSimulator  RailwayBlockOptimizer
```

---

## 3. Provider Abstraction

**File**: `backend/app/ai/provider.py`

```python
class AIProvider(ABC):
    def generate(messages, system_prompt, ...) -> str
    def structured_output(prompt, schema, ...) -> dict
    provider_name: str
```

### Implementations

| Class | When Used | Network |
| :--- | :--- | :--- |
| `MockAIProvider` | `AI_PROVIDER=mock` or unset | None |
| `NvidiaProvider` | `AI_PROVIDER=nvidia` + `AI_API_KEY` set | NVIDIA NIM API |

### Provider Factory

```python
provider = create_ai_provider()   # reads AI_PROVIDER env variable
```

Tomorrow: change one env var, provider swaps automatically.

---

## 4. Tool Registry

**File**: `backend/app/ai/tools.py`

9 tools, each mapping to an existing RailOpt backend capability:

| Tool | Permission | Underlying API |
| :--- | :--- | :--- |
| `get_dashboard_summary` | any auth user | `GET /api/dashboard/summary` |
| `get_maintenance_requests` | any auth user | `GET /api/maintenance/requests` |
| `get_maintenance_request` | any auth user | `GET /api/maintenance/requests/{id}` |
| `get_unscheduled_jobs` | any auth user | `GET /api/maintenance/requests?status=PENDING` |
| `run_optimization` | `can_optimize` | OR-Tools CP-SAT via `RailwayBlockOptimizer` |
| `run_what_if` | `can_optimize` | `WhatIfSimulator` |
| `get_gantt_timeline` | any auth user | `GET /api/gantt/timeline` |
| `get_job_explanation` | any auth user | `DecisionExplainer` |
| `get_reports_analytics` | any auth user | `GET /api/reports/analytics` |

All tools execute by calling **existing services** — zero duplicate business logic.

---

## 5. Role-Aware Permissions (RBAC)

**File**: `backend/app/ai/orchestrator.py`

The orchestrator performs a **pre-check** before executing any tool:

```python
if tool_spec.required_permission:
    if not current_user.get(tool_spec.required_permission, False):
        return refusal_response
```

| Role | `can_optimize` | Can call `run_optimization`/`run_what_if` via AI |
| :--- | :--- | :--- |
| Controller | ✅ | ✅ |
| Planner | ✅ | ✅ |
| Engineer | ❌ | ❌ Refused with message |
| TRD Officer | ❌ | ❌ Refused with message |
| S&T Officer | ❌ | ❌ Refused with message |

**The existing backend endpoints enforce RBAC independently.** The AI pre-check is an additional guard, not a replacement.

---

## 6. Intent Model

**File**: `backend/app/ai/intent.py`

```python
class Intent(str, Enum):
    QUERY      = "query"        # "Show me pending maintenance jobs"
    EXPLAIN    = "explain"      # "Why was JOB-ENG-101 scheduled at 02:10?"
    OPTIMIZE   = "optimize"     # "Run block plan with higher delay priority"
    WHAT_IF    = "what_if"      # "What if Train 12050 is delayed 30 min?"
    REPORT     = "report"       # "Show analytics for the ENG department"
    NAVIGATION = "navigation"   # "Take me to the Gantt chart"
    UNKNOWN    = "unknown"
```

The `IntentClassifier` is **keyword-based** — runs in-process, no LLM call, no latency.

Entity extraction pulls `job_code`, `train_number`, `delay_minutes`, `department_code` from the message for direct tool argument population.

---

## 7. Safety Boundary

**File**: `backend/app/ai/safety.py`

### Prohibited Actions (hardcoded constants)

```python
AI_PROHIBITED_ACTIONS = [
    "direct_db_mutation",
    "bypass_backend_rbac",
    "invent_solver_results",
    "fabricate_train_positions",
    "fabricate_network_data",
    "approve_without_backend_authorization",
    "defer_without_backend_authorization",
    "modify_hard_safety_constraints",
    "claim_feasibility_without_solver_validation",
]
```

### Hard Railway Safety Constraints (documented, never reachable by AI)

```python
HARD_SAFETY_CONSTRAINTS = [
    "machine_exclusivity_no_overlap",       # CP-SAT AddNoOverlap
    "track_line_non_overlap",               # two jobs cannot share track simultaneously
    "train_headway_buffer_minutes",         # minimum passenger train headway gap
    "power_25kv_isolation_synchrony",       # 25kV OHE block synchronisation
    "department_compatibility_matrix",       # shadow block department restrictions
]
```

When data is unavailable, the AI returns `data_unavailable=true` in `ToolCallResult` — never hallucinated data.

---

## 8. Tool Execution Flow

```
User: "Why was JOB-ENG-101 deferred?"

IntentClassifier
  → Intent.EXPLAIN
  → entity: job_code="JOB-ENG-101"

RailOptToolRegistry.get("get_job_explanation")
  → required_permission=None ✓

ToolSpec.execute({"job_code": "JOB-ENG-101"}, db)
  → DecisionExplainer.explain_job_decision("JOB-ENG-101")
  → returns real explanation tree from DB

AIProvider.generate(
  messages=[{"role":"user", "content":"...real data..."}],
  system_prompt="You are RailOpt Copilot..."
)
  → "JOB-ENG-101 was deferred because Section NDL-3 has conflicting 
      passenger train headway constraints at 02:10 per the CP-SAT plan..."

ChatResponse(
  message="...",
  intent=EXPLAIN,
  tool_used="get_job_explanation",
  tool_result=ToolCallResult(data={...real DecisionExplainer data...}),
  action_suggestions=[{"label": "View Decision Audit", "href": "/block-planning"}]
)
```

---

## 9. Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `AI_PROVIDER` | `mock` | `mock` \| `nvidia` \| `anthropic` \| `openai` |
| `AI_API_KEY` | `""` | Provider API key — **never hardcode** |
| `AI_MODEL` | `mock-model` | Model identifier |
| `AI_BASE_URL` | `""` | Override base URL (NVIDIA: `https://integrate.api.nvidia.com/v1`) |

See [.env.example](file:///A:/SHREYAS/RAILWAY%20BLOCK%20AI/.env.example) for full template.

---

## 10. Tomorrow's API Integration Steps (NVIDIA NIM)

1. **Get a free NVIDIA API key** at [https://build.nvidia.com](https://build.nvidia.com) → Sign in → Get API Key

2. **Choose a model** (recommended free tier):
   - `meta/llama-3.1-70b-instruct` — best quality, free
   - `meta/llama-3.1-8b-instruct` — faster, also free

3. **Create `.env`** (copy from `.env.example`):
   ```
   AI_PROVIDER=nvidia
   AI_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxxx
   AI_MODEL=meta/llama-3.1-70b-instruct
   ```

4. **Install the openai SDK** (if not already present):
   ```
   .venv\Scripts\pip install openai
   ```

5. **Restart the server**:
   ```
   .venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
   ```

6. **Verify** at `GET /api/ai/status` — `is_live` should be `true`.

7. **Test the endpoint**:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/ai/chat \
     -H "Authorization: Bearer <your-token>" \
     -H "Content-Type: application/json" \
     -d '{"message": "Why was JOB-ENG-101 scheduled at 02:10?"}'
   ```

No other code changes required — the `NvidiaProvider` class is already implemented and the factory loads it automatically from the env var.

---

## 11. Future UI Contract

The chat UI (to be built in a future sprint) should:

```
User message input
  → POST /api/ai/chat { "message": "...", "context": {...} }
  → ChatResponse
      .message         → display text
      .tool_used       → show "🔧 Used: get_job_explanation"
      .tool_result     → render collapsible raw data panel
      .action_suggestions → show action buttons (Open Gantt, etc.)
      .data_source     → show "live" or "unavailable" badge
```

**Streaming**: Add SSE support later without changing the tool layer.

---

## 12. New Files Created

| File | Purpose |
| :--- | :--- |
| `backend/app/ai/__init__.py` | Package documentation |
| `backend/app/ai/schemas.py` | Pydantic schemas: Intent, ToolCallResult, ChatRequest, ChatResponse |
| `backend/app/ai/safety.py` | Safety boundary constants and helpers |
| `backend/app/ai/provider.py` | AIProvider ABC, MockAIProvider, NvidiaProvider, factory |
| `backend/app/ai/intent.py` | IntentClassifier (keyword-based, no network) |
| `backend/app/ai/tools.py` | RailOptToolRegistry (9 tools, existing backend delegation) |
| `backend/app/ai/orchestrator.py` | AIOrchestrator (intent→tool→RBAC→execute→generate) |
| `backend/app/api/ai_chat.py` | POST /api/ai/chat + GET /api/ai/status |
| `tests/test_ai_architecture.py` | 36 tests — all passing, no network calls |
| `.env.example` | Updated with AI_PROVIDER/AI_API_KEY/AI_MODEL template |

## 13. Existing Files Modified

| File | Change |
| :--- | :--- |
| `backend/app/main.py` | Import and register `ai_chat.router` (2 lines) |
| `backend/app/config.py` | Added AI_PROVIDER, AI_API_KEY, AI_MODEL, AI_BASE_URL fields |
| `.env.example` | Added AI copilot config section |
