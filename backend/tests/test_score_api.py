"""Integration tests for POST /api/score with a faked model."""

import app.scoring as scoring
from app.llm import LLMError

ANALYSIS = {
    "hard_skills": [{"name": "SEO", "aliases": []}],
    "industry_phrases": ["organic traffic"],
    "experience": {
        "min_years": 2,
        "seniority": "specialist",
        "core_domain": "marketing",
        "expects_leadership": False,
    },
}
JUDGMENT = {
    "experience_deductions": [],
    "experience_evidence": "Meets the level.",
    "formatting_deductions": [],
    "formatting_evidence": "Scannable.",
    "skill_credits": [],
    "gaps": [],
}


def fake_llm(monkeypatch):
    monkeypatch.setattr(scoring, "analyze_jd", lambda jd: ANALYSIS)
    monkeypatch.setattr(scoring, "judge_cv", lambda cv, jd, a, m: JUDGMENT)


def upload(client, user_id, fixture_pdf_bytes):
    return client.post(
        "/api/uploads",
        data={"user_id": str(user_id), "jd_text": "Marketing role"},
        files={"cv_file": ("cv.pdf", fixture_pdf_bytes, "application/pdf")},
    )


def test_score_round_trip(client, user_id, fixture_pdf_bytes, monkeypatch):
    fake_llm(monkeypatch)
    upload_response = upload(client, user_id, fixture_pdf_bytes)
    response = client.post("/api/score", json={"upload_id": upload_response.json()["id"]})
    assert response.status_code == 200
    body = response.json()
    assert body["id"] > 0
    assert body["upload_id"] == upload_response.json()["id"]
    assert isinstance(body["overall_score"], int)
    assert body["band"] == scoring.score_band(body["overall_score"])
    assert [b["category"] for b in body["breakdown"]] == [
        scoring.CATEGORY_SKILLS,
        scoring.CATEGORY_EXPERIENCE,
        scoring.CATEGORY_KEYWORDS,
        scoring.CATEGORY_QUANTIFIED,
        scoring.CATEGORY_FORMATTING,
    ]
    assert all(b["evidence"] for b in body["breakdown"])
    assert isinstance(body["matched_keywords"], list)
    assert isinstance(body["missing_keywords"], list)


def test_score_unknown_upload_404(client, monkeypatch):
    fake_llm(monkeypatch)
    response = client.post("/api/score", json={"upload_id": 9999})
    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown upload."


def test_score_model_failure_503(client, user_id, fixture_pdf_bytes, monkeypatch):
    def broken_analysis(jd):
        raise LLMError("Model call failed.")

    monkeypatch.setattr(scoring, "analyze_jd", broken_analysis)
    upload_response = upload(client, user_id, fixture_pdf_bytes)
    response = client.post("/api/score", json={"upload_id": upload_response.json()["id"]})
    assert response.status_code == 503


def test_score_missing_body_422(client):
    response = client.post("/api/score", json={})
    assert response.status_code == 422