"""Unit tests for the code-computed parts of the scoring pipeline."""

from app import scoring


def test_contains_phrase_is_case_insensitive():
    assert scoring._contains_phrase("Led SEO AND CONTENT campaigns", "SEO")
    assert scoring._contains_phrase("grew organic traffic", "Organic Traffic")


def test_contains_phrase_respects_word_boundaries():
    assert not scoring._contains_phrase("wrote javascript widgets", "Java")
    assert scoring._contains_phrase("java services", "Java")
    assert not scoring._contains_phrase("hubspotting", "HubSpot")


def test_match_keywords_uses_aliases():
    skills = [{"name": "Google Analytics 4", "aliases": ["GA4"]}]
    matches = scoring.match_keywords("Built dashboards in GA4", skills, ["A/B testing"])
    assert matches["matched_skills"] == ["Google Analytics 4"]
    assert matches["missing_skills"] == []
    assert matches["missing_phrases"] == ["A/B testing"]


def test_split_bullets():
    text = "Experience\n- Grew traffic 45%\n* Ran 12 campaigns\n2020 Software Engineer"
    bullets = scoring.split_bullets(text)
    assert bullets == ["Grew traffic 45%", "Ran 12 campaigns"]


def test_quantified_score_flags_weak_bullets():
    bullets = ["Grew traffic 45%", "Wrote blog posts", "Cut load time by 30%"]
    score, weak = scoring.quantified_score(bullets)
    assert score == 67
    assert weak == ["Wrote blog posts"]


def test_quantified_score_ignores_dates():
    bullets = ["Migrated platform from 2020 to 2021"]
    score, weak = scoring.quantified_score(bullets)
    assert score == 0
    assert weak == bullets


def test_deduction_score_clamps_at_zero():
    deductions = [{"reason": "no leadership", "points": 25}, {"reason": "junior", "points": 25}]
    assert scoring.weighted_deduction_score(deductions, scoring.MAX_EXPERIENCE_DEDUCTION) == 50


def test_deduction_score_caps_single_points():
    deductions = [{"reason": "model overshot the rubric", "points": 80}]
    assert scoring.weighted_deduction_score(deductions, scoring.MAX_FORMATTING_DEDUCTION) == 85


def test_score_band_boundaries_from_rubric():
    assert scoring.score_band(75) == "strong"
    assert scoring.score_band(74) == "partial"
    assert scoring.score_band(50) == "partial"
    assert scoring.score_band(49) == "weak"


def test_score_texts_assembles_skill_schema(monkeypatch):
    analysis = {
        "hard_skills": [
            {"name": "HubSpot", "aliases": []},
            {"name": "Google Ads", "aliases": []},
        ],
        "industry_phrases": ["cost per acquisition", "organic traffic"],
        "experience": {"min_years": 3, "seniority": "manager", "core_domain": "marketing", "expects_leadership": True},
    }
    judgment = {
        "experience_deductions": [{"reason": "no management evidence", "points": 10}],
        "experience_evidence": "No team management shown.",
        "formatting_deductions": [],
        "formatting_evidence": "Standard sections, scannable bullets.",
        "skill_credits": [{"name": "HubSpot", "credit": 0.5}],
        "gaps": [{"severity": "medium", "evidence": "No marketing automation", "suggestion": "Ask about automation tools"}],
    }
    monkeypatch.setattr(scoring, "analyze_jd", lambda jd: analysis)
    monkeypatch.setattr(scoring, "judge_cv", lambda cv, jd, a, m: judgment)

    result = scoring.score_texts(
        "- Grew organic traffic 45% with Google Ads\n- Wrote blog posts",
        "Marketing manager JD",
    )

    assert set(result) >= {
        "overall_score", "band", "breakdown", "gaps",
        "matched_keywords", "missing_keywords", "weak_bullets",
    }
    by_category = {b["category"]: b for b in result["breakdown"]}
    # Google Ads literal, HubSpot half credit, both phrases matched.
    assert by_category[scoring.CATEGORY_SKILLS]["score"] == 75
    assert by_category[scoring.CATEGORY_KEYWORDS]["score"] == 50
    # One of two bullets quantified, and "Wrote blog posts" flagged weak.
    assert by_category[scoring.CATEGORY_QUANTIFIED]["score"] == 50
    assert result["weak_bullets"] == ["Wrote blog posts"]
    assert by_category[scoring.CATEGORY_EXPERIENCE]["score"] == 90
    assert result["matched_keywords"] == ["Google Ads", "organic traffic"]
    assert result["missing_keywords"] == ["HubSpot", "cost per acquisition"]
    expected = round(sum(b["score"] * b["weight"] / 100 for b in result["breakdown"]))
    assert result["overall_score"] == expected
    assert result["band"] == scoring.score_band(expected)


def test_score_texts_empty_jd_categories_default_high(monkeypatch):
    analysis = {"hard_skills": [], "industry_phrases": [], "experience": {"min_years": None, "seniority": "", "core_domain": "", "expects_leadership": False}}
    judgment = {
        "experience_deductions": [],
        "experience_evidence": "",
        "formatting_deductions": [],
        "formatting_evidence": "",
        "skill_credits": [],
        "gaps": [],
    }
    monkeypatch.setattr(scoring, "analyze_jd", lambda jd: analysis)
    monkeypatch.setattr(scoring, "judge_cv", lambda cv, jd, a, m: judgment)

    result = scoring.score_texts("- Did things", "JD")
    by_category = {b["category"]: b for b in result["breakdown"]}
    assert by_category[scoring.CATEGORY_SKILLS]["score"] == 100
    assert by_category[scoring.CATEGORY_KEYWORDS]["score"] == 100