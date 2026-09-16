## Summary

Implements the scoring core of issue #3 (Chấm điểm và tối ưu CV) — first of three planned PRs. The user can now upload a CV, paste a JD, press Score, and get the weighted score with per-category breakdown, gaps and keyword sets rendered on their own CV.

## Scoring pipeline (hybrid by the compute-in-code rule)

- Code computes everything arithmetic or string matching can answer: literal keyword matching (case-insensitive, alias-aware, word-boundary), the quantified-bullet ratio (any concrete non-year number counts), weighted overall score, band
- Two structured model calls at temperature 0 cover judgment only: a JD analysis (hard skills with aliases, industry phrases, experience requirements) and a CV judgment (experience/formatting deductions with evidence, half-credits for adjacent skills, gaps). Prompts quote `rubric.json` verbatim; the response follows the cv-rubric skill schema
- `backend/app/llm.py` speaks the OpenAI-compatible chat-completions protocol: OpenRouter by default (`OPENROUTER_API_KEY`), or any OpenAI-compatible server via `LLM_BASE_URL`/`LLM_MODEL`/`LLM_API_KEY` in `.env`

## What changed

- `backend/app/llm.py` — new: minimal structured-output client (provider-agnostic)
- `backend/app/scoring.py` — new: pipeline, matcher, bullet quantification, assembly
- `backend/app/main.py` — `POST /api/score` (+ request/response models)
- `backend/app/db.py` — `scores` table (schema still recreated per boot, per current convention)
- `frontend/app/api.ts`, `ScoreResult.tsx`, `highlight.ts`, `app/page.tsx` — Score button, result view: score ring, per-category bars, keyword chips, gap cards, inline CV annotations (matched keywords green, weak bullets amber, missing keywords as red chips)
- `Dockerfile` — ships `rubric.json`; start scripts pass `--env-file .env`
- `CLAUDE.md` — documents the endpoint config and the #3 status

## Test status

- 31 unit + API tests pass (matcher, aliases, word boundaries, bullet quantification, weighting, bands, clamps, endpoint round trip, 404/422/503)
- Frontend builds clean
- `backend/tests/test_scoring_fixtures.py` proves the rubric contract on a live endpoint (skipped without one): asserts all three `expected.json` range/keyword/gap contracts plus score repeatability
- Known open item: the last full fixture calibration run was interrupted before finishing; overall bands and repeatability were verified on a live run, final per-category confirmation is pending. Run `pytest backend/tests/test_scoring_fixtures.py` with a configured endpoint to verify.

## Follow-ups on #3

1. JD link fetching (paste a job-posting URL, we fetch the content)
2. Optimise conversation scoped to found gaps, live preview, result download

Part of #3, does not close it.

🤖 Generated with [Claude Code](https://claude.com/claude-code)