# JobFit

Close the gap between the CV you have and the role you want. Upload a CV, paste a job description, and see how well they match.

## Run

```
scripts/start-windows.ps1      # or start-mac.sh / start-linux.sh
```

The app answers on http://localhost:8000. `scripts/stop-*` removes the container.

## Develop

- `backend/` — FastAPI + SQLite. Install `backend/requirements.txt` into a venv, run `pytest` in `backend/`. Running the server outside Docker requires `JOBFIT_DB_PATH`; the container default is `/data/jobfit.sqlite3`.
- `frontend/` — Next.js, statically exported and served by FastAPI. `npm install && npm run build` produces `out/`.

Packaging: one Docker image (node builds the frontend, python serves it). SQLite lives in the `jobfit-data` volume.