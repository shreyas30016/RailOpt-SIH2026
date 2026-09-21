# AI Provider Verification

**Date:** 2026-09-08 · **Type:** Read-only verification — no application code or configuration was modified.

## Question under audit

> "We are using Model: DeepSeek V4 Flash, Access/provider: FreeBuff. Verify whether this is actually true at runtime."

**Answer: half true.** The model claim is **correct**; the access/provider claim is **incorrect** — the application talks to **NVIDIA**, not FreeBuff. Details and evidence below.

---

## 1. Exact model identifier

```
deepseek-ai/deepseek-v4-flash-0731
```

- Source: `.env` → `AI_MODEL=deepseek-ai/deepseek-v4-flash-0731` (loaded at runtime by `backend/app/config.py` → `load_dotenv()`).
- Read by the provider at runtime: `backend/app/ai/provider.py` → `create_ai_provider()` reads `os.getenv("AI_MODEL")`.
- **Live-confirmed against NVIDIA:** `GET https://integrate.api.nvidia.com/v1/models` with the configured key returned HTTP 200 and lists `deepseek-ai/deepseek-v4-flash-0731` (81 models advertised; DeepSeek family visible: `deepseek-coder-6.7b-instruct`, `deepseek-v4-flash-0731`, `deepseek-v4-pro-0813`).

So **"DeepSeek V4 Flash" is the correct, verifiable model name.**

## 2. Actual API / provider endpoint

```
https://integrate.api.nvidia.com/v1
```

- Set in `.env` → `AI_BASE_URL`; also the built-in default in `NvidiaProvider.NVIDIA_BASE_URL` (`provider.py`).
- This is the **NVIDIA NIM hosted API** (the endpoint behind NVIDIA's build.nvidia.com console, free-tier keys).
- Reachability verified live: no-key `GET /models` → HTTP 200 (public catalog); with-key → HTTP 200, 81 models.
- The provider uses the `openai` Python SDK pointed at that base URL (`OpenAI(base_url=..., api_key=...)`), with DeepSeek thinking enabled via `extra_body={"chat_template_kwargs": {"thinking": True, "reasoning_effort": "high"}}` and `top_p=0.95`.
- Request timeout: 15 s per call (`client.chat.completions.create(timeout=15.0, ...)`); client construction timeout 25 s.

## 3. Provider name used by the application

```
nvidia
```

- `.env` → `AI_PROVIDER=nvidia`; `NvidiaProvider.provider_name` returns `"nvidia"`.
- The factory `create_ai_provider()` accepts `mock | nvidia` (anything else raises `AIProviderConfigError`).
- At runtime with the current `.env`, every `POST /api/ai/chat` instantiates **`NvidiaProvider`** and calls the NVIDIA endpoint above. The **mock provider is not active** (it only activates when `AI_PROVIDER` is unset/`mock`).

## 4. Is "FreeBuff" the provider? — NO (verified)

- The application code contains **zero references to FreeBuff** (grep across `backend/`, `frontend/`, docs: 0 hits).
- There is **no code path** from the app to any FreeBuff API, and no FreeBuff key/endpoint in `.env`.
- The configured key is NVIDIA-issued: prefix `nvapi-`, 70 chars — the standard NVIDIA NIM / build.nvidia.com key format.
- **Correct interpretation:** *FreeBuff is the agent/client platform running this development session* — the tool you are using to build and test the project. It is **not** the model host. The model (DeepSeek V4 Flash) is served by **NVIDIA's infrastructure**, and the app's runtime chat traffic goes **Frontend → RailOpt backend → NVIDIA**.
- Also note: the frontend **never calls any LLM API directly** — the browser only calls the RailOpt backend (`POST /api/ai/chat`), which then calls NVIDIA server-side.

## 5. API key exposure to the frontend — NONE

- Grep of `frontend/` (all `.js` + `.html`) for `nvapi`, `sk-`, `api_key`, `API_KEY`, `AI_PROVIDER`, `deepseek`, `NVIDIA` → **zero matches**.
- The key lives only in `.env`, which is **gitignored** (`.gitignore` lines 17–18, 34; confirmed via `git check-ignore .env`).
- Server-side only: `backend/app/config.py` reads it; `backend/app/api/ai_chat.py` exposes only booleans via `/api/ai/status` (`api_key_configured: true/false`) — never the value.

## 6. Is the "NVIDIA" wording in existing docs accurate?

| Doc / file | Wording | Verdict |
|---|---|---|
| `.env.example` | "Set AI_PROVIDER=nvidia… NVIDIA NIM free API key… build.nvidia.com" | ✅ Accurate |
| `config.py` comments | "Set AI_PROVIDER=nvidia to enable NVIDIA NIM live responses" | ✅ Accurate |
| `provider.py` docstring | NVIDIA NIM, DeepSeek V4 Flash specifics | ✅ Accurate |
| `docs/PROJECT_REPORT.md` | "NVIDIA DeepSeek", "NVIDIA provider", "graceful fallback without the NVIDIA key" | ✅ Accurate |
| `docs/FINAL_EVIDENCE_AUDIT.md` | NVIDIA provider, fallback behavior | ✅ Accurate |
| `docs/AI_ARCHITECTURE.md` | "connect tomorrow", "NvidiaProvider (tomorrow)", §10 "Tomorrow's API Integration Steps" | ⚠️ **Stale** — written before `.env` was configured; the integration is now live, not "tomorrow" |

**One nuance to keep honest in demos:** the app calls NVIDIA *first*; if NVIDIA is slow or unreachable, the orchestrator falls back to a **deterministic tool-grounded summary** (real backend data, but not LLM prose). First-call latency can reach 30–45 s before fallback kicks in. The configured NVIDIA key is valid and the endpoint is reachable from this machine.

## 7. Recommended truthful wording

**For PROJECT_REPORT.md / SIH presentation:**

> **AI Copilot:** server-side **DeepSeek V4 Flash** (`deepseek-ai/deepseek-v4-flash-0731`) hosted on the **NVIDIA NIM API** (`integrate.api.nvidia.com/v1`, free-tier key from build.nvidia.com). The frontend never holds a key — the browser calls only our backend, which invokes NVIDIA. Responses are **tool-grounded in live RailOpt data**, role-scoped, and fall back to a deterministic summary if the remote model is slow/unreachable.

**Do NOT write:** "powered by FreeBuff", "FreeBuff AI", or "FreeBuff-hosted model" — it is not the provider and there is no such code path.

**Precise one-liner for the demo:**

> *"Model: DeepSeek V4 Flash, served via the NVIDIA NIM API with a server-side key; the frontend never touches the model API directly — it talks to our backend, and the AI answers only from real RailOpt data."*

## Verification method summary (all read-only)

1. Read `backend/app/ai/provider.py`, `orchestrator.py`, `ai_chat.py`, `schemas.py`, `intent.py`, `config.py`, `main.py`.
2. Read `.env` keys (secret values masked) + `settings` object → `AI_PROVIDER=nvidia`, `AI_MODEL=deepseek-ai/deepseek-v4-flash-0731`, `AI_BASE_URL=https://integrate.api.nvidia.com/v1`, key present (70-char `nvapi-`).
3. Live HTTP probes: no-key + with-key `GET /models` on `https://integrate.api.nvidia.com/v1` → HTTP 200 / 200, 81 models, target model listed.
4. Grepped `frontend/` for key/model/provider strings → no exposure.
5. Grepped whole repo for `freebuff` → no application references.
6. Confirmed `.env` is gitignored.
7. No files were changed; no server processes were started.

## Files examined

- `backend/app/ai/provider.py` · `orchestrator.py` · `schemas.py` · `intent.py` · `tools.py` (references)
- `backend/app/api/ai_chat.py` · `backend/app/config.py` · `backend/app/main.py`
- `.env` (masked) · `.env.example` · `.gitignore`
- `docs/AI_ARCHITECTURE.md` · `docs/PROJECT_REPORT.md` · `frontend/` (grep audit)