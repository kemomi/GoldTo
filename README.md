# Overseas Jewelry Strategy Simulator

## What This Demo Shows

- A daily strategic brief built from official-source competitor and mall signals
- A Top 1 competitor event chosen by configurable threshold and tie-break rules
- A three-option response simulation: 保持不动 / 局部跟进 / 限时跟进
- Evidence links, manual-review isolation, and threshold tuning

## Repository Layout

- `apps/api`: FastAPI backend
- `apps/web`: React/Vite frontend
- `data`: source manifest, fixture fallbacks, and SQLite database

## Backend Setup

```powershell
cd apps/api
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Frontend Setup

```powershell
cd apps/web
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

## Verification

```powershell
cd apps/api
python -m pytest -v

cd ..\..\apps\web
npm test -- --run
npm run build
```

## Demo Flow

1. Open the app and show the daily brief.
2. Click the Hong Kong top event generated from a real or fallback official source.
3. Ask the three canned judging questions.
4. Trigger simulation and explain why `局部跟进` wins.
5. Adjust thresholds to show the event scoring is configurable.
