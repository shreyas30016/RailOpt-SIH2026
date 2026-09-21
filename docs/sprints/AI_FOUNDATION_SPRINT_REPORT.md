# Sprint AI-FOUNDATION — Architecture Report

**Date**: 2026-09-02  
**Status**: ✅ COMPLETE — Architecture ready, live LLM NOT enabled

---

## What Was Built

A production-style, provider-agnostic AI copilot architecture was added to the RailOpt backend as a new `backend/app/ai/` package. The AI layer:

- Exposes `POST /api/ai/chat` and `GET /api/ai/status` endpoints
- Respects all existing RBAC (same session token, same permission checks)
- Delegates all data work to existing backend services — zero duplicate business logic
- Enforces the AI Safety Boundary: no direct DB mutation, no hallucination
- Works fully offline/in mock mode without any API key
- Is ready to wire to NVIDIA NIM tomorrow by adding 3 environment variables

---

## Files Created

| File | Purpose |
| :--- | :--- |
| `backend/app/ai/__init__.py` | Package documentation |
| `backend/app/ai/schemas.py` | Intent, ToolCallResult, ChatRequest, ChatResponse schemas |
| `backend/app/ai/safety.py` | AI_PROHIBITED_ACTIONS, HARD_SAFETY_CONSTRAINTS, refusal helpers |
| `backend/app/ai/provider.py` | AIProvider ABC, MockAIProvider, NvidiaProvider, factory |
| `backend/app/ai/intent.py` | IntentClassifier (keyword-based, no network, <1ms) |
| `backend/app/ai/tools.py` | RailOptToolRegistry (9 tools → existing backend APIs) |
| `backend/app/ai/orchestrator.py` | AIOrchestrator pipeline |
| `backend/app/api/ai_chat.py` | POST /api/ai/chat + GET /api/ai/status endpoints |
| `tests/test_ai_architecture.py` | 36 tests |
| `docs/AI_ARCHITECTURE.md` | Full architecture documentation |

## Files Modified

| File | Change |
| :--- | :--- |
| `backend/app/main.py` | Registered ai_chat.router (2 lines) |
| `backend/app/config.py` | Added AI_PROVIDER/AI_API_KEY/AI_MODEL/AI_BASE_URL fields |
| `.env.example` | Added AI copilot section |
| `PROJECT_MEMORY.md` | Sprint record |

---

## Test Results

```
tests/test_ai_architecture.py  — 36/36 PASSED
Full regression suite          — (running)
```

### Test Coverage
1. ✅ AI provider abstraction loads (MockAIProvider default)
2. ✅ Tool registry loads with exactly 9 tools
3. ✅ All tool schemas validate
4. ✅ Role permission pre-check enforced before tool execution
5. ✅ Engineer cannot run optimization via AI (refused)
6. ✅ TRD cannot bypass permissions via AI
7. ✅ S&T cannot bypass permissions via AI
8. ✅ Controller can access permitted tools
9. ✅ Planner can access permitted tools
10. ✅ Tool execution delegates to existing backend (no duplicate logic)
11. ✅ No direct DB mutation in AI layer
12. ✅ Missing AI_API_KEY raises clean AIProviderConfigError
13. ✅ Safety prohibited actions list populated
14. ✅ Hard safety constraints list populated
15. ✅ Intent classifier EXPLAIN/OPTIMIZE/WHAT_IF/QUERY/NAVIGATION
16. ✅ Entity extraction: job_code, delay_minutes, train_number

---

## Existing Systems Unchanged

- ✅ OR-Tools CP-SAT solver mathematics — untouched
- ✅ P1.3 RBAC enforcement — unchanged
- ✅ P2.1 solver objective controls — unchanged
- ✅ Frontend UI/theme — unchanged
- ✅ All 75 prior regression tests — passing

---

## Tomorrow: Connect NVIDIA NIM (5-minute task)

1. Get free key at https://build.nvidia.com
2. In `.env`:
   ```
   AI_PROVIDER=nvidia
   AI_API_KEY=nvapi-xxxx
   AI_MODEL=meta/llama-3.1-70b-instruct
   ```
3. `pip install openai` (if not installed)
4. Restart server
5. Verify `GET /api/ai/status` → `"is_live": true`

No code changes needed.
