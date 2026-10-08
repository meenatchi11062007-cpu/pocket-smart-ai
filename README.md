# PocketSmart AI — Complete Project

FastAPI + Jinja2 + SQLite + Google Gemini recommendation assistant matching the supplied documentation.

## Features
- Registration/login/logout and JWT token endpoint
- Dashboard and recommendation history
- Home Interior Planner
- Party Budget Planner
- Jewelry Planner with optional outfit image
- Gemini multimodal integration
- Demo fallback when API access is unavailable
- Responsive UI
- SQLite persistence

## Windows PowerShell
```powershell
cd PocketSmartAI
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000

If activation is blocked: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

## Gemini
Put your key in `.env` as `GEMINI_API_KEY=...`. Set `DEMO_MODE=false` to use Gemini. `GEMINI_MODEL` is configurable and defaults to `gemini-3.8-flash`.

The supplied document names Gemini 1.5 Flash Pro; this implementation uses the current Google GenAI SDK/model configuration while keeping the model setting editable.

## Test
`pytest -q`

## Main routes
`/`, `/register`, `/login`, `/logout`, `/token`, `/dashboard`, `/planner/home`, `/planner/party`, `/planner/jewelry`, `/generate-home`, `/generate-party`, `/generate-jewelry`, `/recommendations-details/{id}`, `/history`, `/session-info`, `/session-data`, `/startup`, `/health`.

Product/platform links are search links. The supplied documentation calls for mock/simulated sourcing, so the app does not pretend to have live inventory from Amazon, Flipkart, IKEA, Swiggy, Zomato or OYO.
