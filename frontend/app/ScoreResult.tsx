"use client";

import { ScoreGap, ScoreResult as ApiScoreResult, ScoreBreakdownItem } from "./api";
import { buildLineSegments, Segment } from "./highlight";

/** Score colour is meaning: band thresholds come from rubric.json score_bands. */
export function scoreColour(score: number): string {
  if (score >= 75) return "var(--strong)";
  if (score >= 50) return "var(--partial)";
  return "var(--weak)";
}

function scoreRing(score: number): React.ReactElement {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const filled = (Math.max(0, Math.min(100, score)) / 100) * circumference;
  const colour = scoreColour(score);
  return (
    <svg viewBox="0 0 120 120" className="h-36 w-36" role="img" aria-label={`Overall score ${score} of 100`}>
      <circle cx="60" cy="60" r={radius} fill="none" stroke="#e5e7eb" strokeWidth="12" />
      <circle
        cx="60"
        cy="60"
        r={radius}
        fill="none"
        stroke={colour}
        strokeWidth="12"
        strokeLinecap="round"
        strokeDasharray={`${filled} ${circumference - filled}`}
        transform="rotate(-90 60 60)"
      />
      <text x="60" y="56" textAnchor="middle" fontSize="30" fontWeight="bold" fill={colour}>
        {score}
      </text>
      <text x="60" y="78" textAnchor="middle" fontSize="11" fill="var(--muted)">
        of 100
      </text>
    </svg>
  );
}

function categoryBar(item: ScoreBreakdownItem): React.ReactElement {
  return (
    <div key={item.category}>
      <div className="flex items-baseline justify-between text-sm">
        <span className="font-medium" style={{ color: "var(--ink)" }}>
          {item.category}
          <span className="ml-2 font-normal" style={{ color: "var(--muted)" }}>
            weight {item.weight}%
          </span>
        </span>
        <span className="font-bold" style={{ color: scoreColour(item.score) }}>
          {item.score}
        </span>
      </div>
      <div className="mt-1 h-2 w-full overflow-hidden rounded bg-gray-100">
        <div
          className="h-full rounded"
          style={{ width: `${item.score}%`, background: scoreColour(item.score) }}
        />
      </div>
      <p className="mt-1 text-xs" style={{ color: "var(--muted)" }}>
        {item.evidence}
      </p>
    </div>
  );
}

const SEVERITY_COLOUR: Record<string, string> = {
  high: "var(--weak)",
  medium: "var(--partial)",
  low: "var(--muted)",
};

function gapCard(gap: ScoreGap, index: number): React.ReactElement {
  return (
    <li
      key={index}
      className="rounded border-l-4 bg-gray-50 p-3 text-sm"
      style={{ borderColor: SEVERITY_COLOUR[gap.severity] ?? "var(--muted)" }}
    >
      <p className="font-medium capitalize" style={{ color: "var(--ink)" }}>
        {gap.severity} gap
      </p>
      <p style={{ color: "var(--ink)" }}>{gap.evidence}</p>
      <p className="mt-1" style={{ color: "var(--muted)" }}>
        Suggestion: {gap.suggestion}
      </p>
    </li>
  );
}

function keywordChips(title: string, keywords: string[], colour: string): React.ReactElement {
  return (
    <div>
      <p className="text-sm font-medium" style={{ color: "var(--ink)" }}>
        {title}
      </p>
      <div className="mt-1 flex flex-wrap gap-1.5">
        {keywords.length === 0 && (
          <span className="text-sm" style={{ color: "var(--muted)" }}>
            None
          </span>
        )}
        {keywords.map((keyword) => (
          <span
            key={keyword}
            className="rounded-full px-2.5 py-0.5 text-xs font-medium text-white"
            style={{ background: colour }}
          >
            {keyword}
          </span>
        ))}
      </div>
    </div>
  );
}

function highlightedCv(cvText: string, result: ApiScoreResult): React.ReactElement {
  const lines = buildLineSegments(cvText, result.matched_keywords, result.weak_bullets);
  return (
    <pre className="mt-2 max-h-[32rem] overflow-auto whitespace-pre-wrap rounded border border-gray-200 bg-gray-50 p-4 text-sm leading-relaxed">
      {lines.map((segments, index) => (
        <div key={index}>
          {segments.map((segment: Segment, segmentIndex: number) => (
            <span
              key={segmentIndex}
              style={
                segment.kind === "matched"
                  ? { background: "var(--strong)", color: "#ffffff", borderRadius: 3, padding: "0 2px" }
                  : segment.kind === "weak"
                    ? { background: "var(--partial)", color: "#ffffff", borderRadius: 3, padding: "0 2px" }
                    : { color: "var(--ink)" }
              }
            >
              {segment.text}
            </span>
          ))}
          {"\n"}
        </div>
      ))}
    </pre>
  );
}

export default function ScoreResultView({
  result,
  cvText,
}: {
  result: ApiScoreResult;
  cvText: string;
}) {
  return (
    <section className="mt-8 flex flex-col gap-8">
      <div className="flex flex-wrap items-center gap-6">
        {scoreRing(result.overall_score)}
        <div>
          <h2 className="text-xl font-bold capitalize" style={{ color: scoreColour(result.overall_score) }}>
            {result.band} match
          </h2>
          <p className="text-sm" style={{ color: "var(--muted)" }}>
            Weighted across five categories from the scoring rubric.
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        {result.breakdown.map(categoryBar)}
      </div>

      <div className="flex flex-col gap-4 md:flex-row">
        {keywordChips("Matched keywords", result.matched_keywords, "var(--strong)")}
        {keywordChips("Missing keywords", result.missing_keywords, "var(--weak)")}
      </div>

      <div>
        <h3 className="text-base font-semibold" style={{ color: "var(--ink)" }}>
          Gaps to close
        </h3>
        {result.gaps.length === 0 ? (
          <p className="mt-2 text-sm" style={{ color: "var(--muted)" }}>
            No gaps found.
          </p>
        ) : (
          <ul className="mt-2 flex list-none flex-col gap-2 pl-0">
            {result.gaps.map(gapCard)}
          </ul>
        )}
      </div>

      <div>
        <h3 className="text-base font-semibold" style={{ color: "var(--ink)" }}>
          Your CV, annotated
        </h3>
        <p className="text-xs" style={{ color: "var(--muted)" }}>
          Green marks matched keywords. Amber marks bullets without measurable
          results. Red chips above list what is absent entirely.
        </p>
        {highlightedCv(cvText, result)}
      </div>
    </section>
  );
}