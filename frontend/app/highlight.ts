/** Builds inline highlight segments for the CV preview.

Matched keywords render in the strong colour, weak (non-quantified) bullets
in the partial colour; everything else stays plain. Lines come back as an
array of segment arrays so the preview can render one row per CV line.
*/

export type SegmentKind = "plain" | "matched" | "weak";

export interface Segment {
  text: string;
  kind: SegmentKind;
}

const BULLET_PREFIX = /^[\s>]*(?:[-*•‣◦⁃·]|\d+[.)])\s+/;

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function keywordPattern(keywords: string[]): RegExp | null {
  const cleaned = keywords
    .filter((k) => k.trim().length > 0)
    .sort((a, b) => b.length - a.length)
    .map(escapeRegExp);
  if (cleaned.length === 0) return null;
  return new RegExp(`(?<![a-z0-9])(${cleaned.join("|")})(?![a-z0-9])`, "gi");
}

export function buildLineSegments(
  cvText: string,
  matchedKeywords: string[],
  weakBullets: string[],
): Segment[][] {
  const weak = new Set(weakBullets.map((b) => b.trim().toLowerCase()));
  const pattern = keywordPattern(matchedKeywords);
  const lines: Segment[][] = [];

  for (const line of cvText.split("\n")) {
    const bulletText = line.replace(BULLET_PREFIX, "").trim().toLowerCase();
    const baseKind: SegmentKind = weak.has(bulletText) ? "weak" : "plain";
    const segments: Segment[] = [];
    if (pattern !== null) {
      let last = 0;
      for (const match of line.matchAll(pattern)) {
        const start = match.index ?? 0;
        if (start > last) segments.push({ text: line.slice(last, start), kind: baseKind });
        segments.push({ text: match[0], kind: "matched" });
        last = start + match[0].length;
      }
      if (last < line.length) segments.push({ text: line.slice(last), kind: baseKind });
    } else {
      segments.push({ text: line, kind: baseKind });
    }
    lines.push(segments);
  }
  return lines;
}