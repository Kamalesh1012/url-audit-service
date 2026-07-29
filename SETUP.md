# Setup Guide — Windows + VS Code + Python 3.12

Step-by-step to get `url-audit-service` from zip file to a running local
service, pushed to GitHub with CI passing, and deployed live.

## 1. Create and clone the repo

1. Go to github.com → **New repository** → name it `url-audit-service` →
   Create (don't add a README — this project already has one).
2. Open PowerShell (or VS Code's integrated terminal):

```powershell
cd C:\Users\<you>\Projects
git clone https://github.com/<your-username>/url-audit-service.git
cd url-audit-service
```

## 2. Drop the project in

Unzip this project and copy everything from inside the `url-audit-service/`
folder (not the folder itself) into the cloned repo folder, so `app/`,
`tests/`, `README.md`, etc. sit directly alongside the `.git` folder.

Open the folder in VS Code:

```powershell
code .
```

Install the **Python extension** if VS Code prompts you.

## 3. Virtual environment + dependencies

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script, run this once first:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then install dependencies:

```powershell
pip install -r requirements-dev.txt
```

In VS Code: `Ctrl+Shift+P` → **Python: Select Interpreter** → pick the one
at `.\venv\Scripts\python.exe`.

## 4. Redis (for running the live server; tests don't need it)

Easiest route on Windows is Docker:

```powershell
docker run -d -p 6379:6379 redis
```

No Docker? Install Docker Desktop, or skip this step for now — `pytest`
uses an in-memory fake cache, so the test suite runs without a real Redis
instance. Only running the live server (`uvicorn`) needs Redis.

## 5. Run the tests

```powershell
copy .env.example .env
pytest -v
```

## 6. Run it locally

```powershell
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs` for interactive API docs.

## 7. Commit and push

```powershell
git add .
git commit -m "Production-grade URL audit service (Task A) + scale architecture (Task B)"
git push origin main
```

Pushing triggers `.github/workflows/ci.yml` automatically — check the
**Actions** tab on GitHub to confirm it's green.

## 8. Deploy for the live URL

Sign up at render.com → **New** → **Blueprint** → connect your repo →
Render reads `render.yaml` and provisions the web service + Redis
automatically.

Once live, confirm the footer credit line the brief requires ("Built for
Digital Heroes Training Task", linked to digitalheroesco.com) renders
correctly — it's already wired into the `/` route in `app/main.py`; double
check placement if you build a frontend on top of the API.

## Troubleshooting

- **`py -3.12` not found** — reinstall Python 3.12 from python.org and
  check "Add to PATH" during install, or use `python --version` to confirm
  what's on PATH.
- **`pip install` fails on a package** — run `pip install --upgrade pip`
  first, then retry.
- **`pytest` can't import `app`** — make sure you're running it from the
  repo root (the folder containing `app/` and `tests/`), not from inside
  `app/`.
- **CI is red on GitHub but tests pass locally** — check the Actions log;
  the most common cause is a dependency version mismatch, since CI installs
  fresh from `requirements-dev.txt` every time.
