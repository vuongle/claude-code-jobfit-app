"""CV scoring pipeline.

Split by the rule that anything arithmetic or string matching can answer is
computed in code; only evidence-based judgment goes through the model. The
final result follows the structured output schema from the cv-rubric skill,
and every scoring rule quoted in the prompts comes verbatim from rubric.json.
"""

import json
import os
import re
from functools import lru_cache

from . import llm

CATEGORY_SKILLS = "Hard Skills Match"
CATEGORY_EXPERIENCE = "Experience Match"
CATEGORY_KEYWORDS = "ATS Keywords"
CATEGORY_QUANTIFIED = "Quantified Achievements"
CATEGORY_FORMATTING = "Formatting & Length"

JD_ANALYSIS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["hard_skills", "industry_phrases", "experience"],
    "properties": {
        "hard_skills": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "aliases"],
                "properties": {
                    "name": {"type": "string"},
                    "aliases": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "industry_phrases": {"type": "array", "items": {"type": "string"}},
        "experience": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "min_years",
                "seniority",
                "core_domain",
                "expects_leadership",
            ],
            "properties": {
                "min_years": {"type": ["integer", "null"]},
                "seniority": {"type": "string"},
                "core_domain": {"type": "string"},
                "expects_leadership": {"type": "boolean"},
            },
        },
    },
}

_DEDUCTION_ITEMS = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["reason", "points"],
        "properties": {
            "reason": {"type": "string"},
            "points": {"type": "integer"},
        },
    },
}

JUDGMENT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "experience_deductions",
        "experience_evidence",
        "formatting_deductions",
        "formatting_evidence",
        "skill_credits",
        "gaps",
    ],
    "properties": {
        "experience_deductions": _DEDUCTION_ITEMS,
        "experience_evidence": {"type": "string"},
        "formatting_deductions": _DEDUCTION_ITEMS,
        "formatting_evidence": {"type": "string"},
        "skill_credits": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "credit"],
                "properties": {
                    "name": {"type": "string"},
                    "credit": {"type": "number", "enum": [0, 0.5]},
                },
            },
        },
        "gaps": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["severity", "evidence", "suggestion"],
                "properties": {
                    "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                    "evidence": {"type": "string"},
                    "suggestion": {"type": "string"},
                },
            },
        },
    },
}

BULLET_PREFIX = re.compile(r"^[\s>]*(?:[-*•‣◦⁃·]|\d+[.)])\s+")

MAX_EXPERIENCE_DEDUCTION = 25
MAX_FORMATTING_DEDUCTION = 15


@lru_cache(maxsize=1)
def rubric() -> dict:
    """Load rubric.json, the single source of truth for weights and rules."""
    path = os.environ.get(
        "JOBFIT_RUBRIC_PATH",
        os.path.join(os.path.dirname(__file__), "..", "..", "rubric.json"),
    )
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def category_weights() -> dict[str, int]:
    return {c["name"]: c["weight"] for c in rubric()["categories"]}


def score_band(score: int) -> str:
    for band in rubric()["score_bands"]:
        if band["min"] <= score <= band["max"]:
            return band["name"]
    raise ValueError(f"Score {score} outside every band.")


# --- code-computed measurements ---


def _contains_phrase(haystack: str, phrase: str) -> bool:
    """Case-insensitive whole-word search (so Java does not match JavaScript)."""
    needle = re.sub(r"\s+", " ", phrase).strip().lower()
    if not needle:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])"
    return re.search(pattern, haystack.lower()) is not None


def match_keywords(cv_text: str, hard_skills: list, phrases: list) -> dict:
    """Literal keyword matching per rubric keyword_rules; alias-aware for skills."""
    norm_cv = re.sub(r"\s+", " ", cv_text.lower())
    matched, missing_skills = [], []
    for skill in hard_skills:
        candidates = [skill["name"], *skill.get("aliases", [])]
        if any(_contains_phrase(norm_cv, c) for c in candidates):
            matched.append(skill["name"])
        else:
            missing_skills.append(skill["name"])
    matched_phrases = [p for p in phrases if _contains_phrase(norm_cv, p)]
    missing_phrases = [p for p in phrases if p not in matched_phrases]
    return {
        "matched_skills": matched,
        "missing_skills": missing_skills,
        "matched_phrases": matched_phrases,
        "missing_phrases": missing_phrases,
    }


def split_bullets(cv_text: str) -> list[str]:
    return [
        BULLET_PREFIX.sub("", line).strip()
        for line in cv_text.splitlines()
        if BULLET_PREFIX.match(line)
    ]


def _has_measure(bullet: str) -> bool:
    """True when the bullet carries a concrete number that is not a bare year.

    The rubric counts any number representing an outcome, scale or improvement:
    counts, percentages, durations, currency. A lone year (2020) is a date, not
    a measure.
    """
    return any(
        not re.fullmatch(r"(?:19|20)\d{2}", match)
        for match in re.findall(r"\d+", bullet)
    )


def quantified_score(bullets: list[str]) -> tuple[int, list[str]]:
    """Return (percentage of quantified bullets, the non-quantified bullets)."""
    weak = [b for b in bullets if not _has_measure(b)]
    if not bullets:
        return 0, []
    return round(100 * (len(bullets) - len(weak)) / len(bullets)), weak


def weighted_deduction_score(deductions: list, cap: int) -> int:
    total = sum(max(0, min(int(d["points"]), cap)) for d in deductions)
    return max(0, 100 - total)


# --- model calls ---


def analyze_jd(jd_text: str) -> dict:
    system = (
        "You extract structured requirements from job descriptions for a CV scoring "
        "tool that follows the cv-rubric skill.\n"
        "hard_skills: the named tools, languages, frameworks, platforms and products "
        "the JD requires (for example Stripe, Kubernetes, HubSpot, GA4), each with "
        "explicit alias equivalents (GA4 for Google Analytics 4). Use canonical names. "
        "When the JD pairs a product with its generic category ('a CRM such as "
        "Salesforce'), extract the category as its own term too ('CRM').\n"
        "industry_phrases: the short domain terminology an applicant tracking system "
        "would search for, beyond named tools. Rules:\n"
        "- 1 to 4 words, and prefer the shortest form that still names the concept: "
        "'REST API', 'idempotent' (not 'idempotent flows'), 'event-driven' (not "
        "'event-driven architecture'), 'payment gateway', 'organic traffic', "
        "'e-commerce', 'A/B testing', 'cost per acquisition'.\n"
        "- Copy the JD's core term verbatim; never paraphrase, never merge into a "
        "requirement sentence, never append qualifiers such as 'at scale' or 'such "
        "as Salesforce', never include parenthetical lists.\n"
        "- Prefer the plain noun when the JD leans on a generic channel or concept "
        "repeatedly: 'email', 'CRM', 'budget', 'attribution', 'segmentation'.\n"
        "- Extract only concrete, repeatable terms (roughly 8 to 15 phrases), not "
        "descriptive clauses like 'checkout and settlement pipelines' or 'lifecycle "
        "flows' unless that exact phrase is established industry terminology.\n"
        "experience: min_years is an integer or null when the JD states no years of "
        "experience; seniority is the level the JD targets; core_domain is the "
        "industry or domain in one or two words; expects_leadership is true when the "
        "JD expects managing people.\n"
        "Include only requirements actually stated or clearly implied by the JD. Do "
        "not invent requirements."
    )
    return llm.structured_call(system, jd_text, JD_ANALYSIS_SCHEMA)


def judge_cv(cv_text: str, jd_text: str, analysis: dict, matches: dict) -> dict:
    rules = rubric()
    rules_by_name = {c["name"]: c for c in rules["categories"]}
    system = (
        "You judge a CV against analysed job description requirements under the "
        "cv-rubric skill. Apply these scoring rules verbatim:\n"
        f"{CATEGORY_EXPERIENCE}: {rules_by_name[CATEGORY_EXPERIENCE]['scoring_rule']}\n"
        f"{CATEGORY_FORMATTING}: {rules_by_name[CATEGORY_FORMATTING]['scoring_rule']}\n"
        "Gap rules: " + rules["gap_rules"]["definition"] + "\n"
        "Gap severities: " + json.dumps(rules["gap_rules"]["severities"]) + "\n"
        "NEVER FABRICATE: every suggestion must be concrete and must not invent "
        "numbers, employers, technologies or achievements the CV does not mention. "
        "When the CV lacks the information needed for a suggestion, say what to ask "
        "the candidate instead. For skill_credits, list every missing skill that the "
        "CV gives adjacent or entry-level evidence of with credit 0.5, and omit the "
        "rest (they stay at 0)."
    )
    user = json.dumps(
        {
            "jd_text": jd_text,
            "jd_analysis": analysis,
            "literal_keyword_matches": matches,
            "cv_text": cv_text,
        }
    )
    return llm.structured_call(system, user, JUDGMENT_SCHEMA)


# --- assembly ---


def _evidence_for_skills(total: int, matched: list, half: list) -> str:
    parts = [f"{len(matched)} of {total} required hard skills appear literally in the CV."]
    if half:
        parts.append(f"Adjacent or entry-level evidence (half credit): {', '.join(half)}.")
    return " ".join(parts)


def _evidence_for_keywords(total: int, matched: list) -> str:
    detail = f": {', '.join(matched)}." if matched else "."
    return f"{len(matched)} of {total} keywords (hard skills and industry phrases) appear in the CV{detail}"


def score_texts(cv_text: str, jd_text: str) -> dict:
    """Score one CV against one JD and return the cv-rubric structured result."""
    weights = category_weights()
    analysis = analyze_jd(jd_text)
    matches = match_keywords(cv_text, analysis["hard_skills"], analysis["industry_phrases"])
    judgment = judge_cv(cv_text, jd_text, analysis, matches)

    total_skills = len(analysis["hard_skills"])
    half_names = []
    credits = {
        c["name"].lower(): c["credit"]
        for c in judgment.get("skill_credits", [])
    }
    for name in matches["missing_skills"]:
        credit = credits.get(name.lower())
        if credit == 0.5:
            half_names.append(name)
    skills_score = (
        round(100 * (len(matches["matched_skills"]) + 0.5 * len(half_names)) / total_skills)
        if total_skills
        else 100
    )

    # ATS Keywords counts the full keyword set (hard skills + industry phrases),
    # per rubric.json keyword_rules which defines matched_keywords as exactly that
    # merge. Hard Skills Match scores tool coverage separately.
    all_phrases = len(matches["matched_phrases"]) + len(matches["missing_phrases"])
    all_keywords = len(analysis["hard_skills"]) + all_phrases
    keywords_matched = len(matches["matched_skills"]) + len(matches["matched_phrases"])
    keywords_score = round(100 * keywords_matched / all_keywords) if all_keywords else 100

    bullets = split_bullets(cv_text)
    quant_score, weak_bullets = quantified_score(bullets)

    experience_score = weighted_deduction_score(
        judgment["experience_deductions"], MAX_EXPERIENCE_DEDUCTION
    )
    formatting_score = weighted_deduction_score(
        judgment["formatting_deductions"], MAX_FORMATTING_DEDUCTION
    )

    scores = {
        CATEGORY_SKILLS: (skills_score, _evidence_for_skills(total_skills, matches["matched_skills"], half_names)),
        CATEGORY_EXPERIENCE: (experience_score, judgment["experience_evidence"]),
        CATEGORY_KEYWORDS: (keywords_score, _evidence_for_keywords(all_keywords, matches["matched_skills"] + matches["matched_phrases"])),
        CATEGORY_QUANTIFIED: (
            quant_score,
            f"{len(bullets) - len(weak_bullets)} of {len(bullets)} bullets contain a "
            "measurable outcome number.",
        ),
        CATEGORY_FORMATTING: (formatting_score, judgment["formatting_evidence"]),
    }
    overall = round(
        sum(scores[name][0] * weights[name] / 100 for name in weights)
    )

    return {
        "overall_score": overall,
        "band": score_band(overall),
        "breakdown": [
            {"category": name, "score": scores[name][0], "weight": weights[name], "evidence": scores[name][1]}
            for name in weights
        ],
        "gaps": judgment["gaps"],
        "matched_keywords": matches["matched_skills"] + matches["matched_phrases"],
        "missing_keywords": matches["missing_skills"] + matches["missing_phrases"],
        "weak_bullets": weak_bullets,
    }