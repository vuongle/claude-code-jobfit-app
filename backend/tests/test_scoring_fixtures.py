"""Fixture-based scoring tests: prove the rubric behaves consistently.

These run the real pipeline against fixtures/ and assert the expectations
each case ships in expected.json. They need a reachable LLM endpoint: an
OPENROUTER_API_KEY for the default OpenRouter route, or any OpenAI-compatible
server via LLM_BASE_URL in .env. Without either they are skipped so unit and
API suites still run.
"""

import json
import os

import pytest

from app import scoring
from app.llm import DEFAULT_BASE_URL, load_env

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "fixtures")
SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2}


def pytest_collection_modifyitems(config, items):
    load_env()
    base = os.environ.get("LLM_BASE_URL")
    has_endpoint = bool(
        os.environ.get("OPENROUTER_API_KEY")
        or os.environ.get("LLM_API_KEY")
        or (base is not None and base != DEFAULT_BASE_URL)
    )
    if has_endpoint:
        return
    skip = pytest.mark.skip(reason="No LLM endpoint configured (OPENROUTER_API_KEY or LLM_BASE_URL)")
    for item in items:
        if item.fspath.basename == "test_scoring_fixtures.py":
            item.add_marker(skip)


def read_fixture(*parts: str) -> str:
    with open(os.path.join(FIXTURES_DIR, *parts), encoding="utf-8") as fh:
        return fh.read()


def load_cases():
    with open(os.path.join(FIXTURES_DIR, "index.json"), encoding="utf-8") as fh:
        index = json.load(fh)
    cases = []
    for case in index["cases"]:
        with open(os.path.join(FIXTURES_DIR, case["expected"]), encoding="utf-8") as fh:
            expected = json.load(fh)
        cases.append((case["id"], read_fixture(*case["cv"].split("/")), read_fixture(*case["jd"].split("/")), expected))
    return cases


CASES = load_cases()


def keyword_present(keywords: set[str], keyword: str) -> bool:
    """Rubric keyword_rules allow 'close literal variants', so a fixture keyword
    matches an extracted keyword that contains it or is contained in it."""
    kw = keyword.lower()
    return any(kw in candidate or candidate in kw for candidate in keywords)


@pytest.mark.parametrize("case_id,cv,jd,expected", CASES, ids=[c[0] for c in CASES])
def test_fixture_scores_match_expected(case_id, cv, jd, expected):
    result = scoring.score_texts(cv, jd)

    low, high = expected["overall_score_range"]
    assert low <= result["overall_score"] <= high, (
        f"overall {result['overall_score']} outside [{low}, {high}]"
    )
    assert result["band"] == expected["band"]

    by_category = {b["category"]: b for b in result["breakdown"]}
    for category, (cat_low, cat_high) in expected["category_score_ranges"].items():
        score = by_category[category]["score"]
        assert cat_low <= score <= cat_high, f"{category} {score} outside [{cat_low}, {cat_high}]"

    matched = {k.lower() for k in result["matched_keywords"]}
    for keyword in expected["required_matched_keywords"]:
        assert keyword_present(matched, keyword), f"{keyword} not matched"

    missing = {k.lower() for k in result["missing_keywords"]}
    for keyword in expected["required_missing_keywords"]:
        assert keyword_present(missing, keyword), f"{keyword} wrongly matched"

    for required in expected["required_gaps"]:
        topic_gaps = [
            g
            for g in result["gaps"]
            if any(phrase in g["evidence"].lower() for phrase in required["evidence_must_include_any"])
        ]
        assert topic_gaps, f"no gap covers topic {required['topic']}"
        best = max(SEVERITY_ORDER[g["severity"]] for g in topic_gaps)
        assert best >= SEVERITY_ORDER[required["min_severity"]], (
            f"topic {required['topic']} never reaches severity {required['min_severity']}"
        )

    high_count = sum(1 for g in result["gaps"] if g["severity"] == "high")
    assert high_count <= expected["max_high_severity_gaps"]


def test_scoring_is_repeatable_for_demo_case():
    """Same CV and same JD produce the same score, every time."""
    cv = read_fixture("case-02-marketing-partial", "cv.md")
    jd = read_fixture("case-02-marketing-partial", "jd.md")
    first = scoring.score_texts(cv, jd)
    second = scoring.score_texts(cv, jd)
    assert first["overall_score"] == second["overall_score"]
    assert first["breakdown"] == second["breakdown"]
    assert first["matched_keywords"] == second["matched_keywords"]
    assert first["missing_keywords"] == second["missing_keywords"]