"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ScoreResult, UploadResult, scoreUpload, uploadCv } from "../api";
import { clearUserId, getUserId } from "../session";
import ScoreResultView from "../ScoreResult";

export default function AppPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState("");
  const [result, setResult] = useState<UploadResult | null>(null);
  const [score, setScore] = useState<ScoreResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [scoring, setScoring] = useState(false);

  useEffect(() => {
    if (getUserId() === null) {
      router.replace("/");
    }
  }, [router]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!file) return;
    setError(null);
    setResult(null);
    setScore(null);
    setBusy(true);
    try {
      const userId = getUserId();
      if (userId === null) throw new Error("Session expired. Please sign in again.");
      setResult(await uploadCv(userId, file, jdText));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  async function handleScore() {
    if (!result) return;
    setError(null);
    setScore(null);
    setScoring(true);
    try {
      setScore(await scoreUpload(result.id));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Something went wrong.");
    } finally {
      setScoring(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col px-6 py-10">
      <header className="flex items-baseline justify-between">
        <h1 className="text-2xl font-bold" style={{ color: "var(--ink)" }}>
          JobFit
        </h1>
        <button
          type="button"
          onClick={() => {
            clearUserId();
            router.push("/");
          }}
          className="text-sm"
          style={{ color: "var(--primary)" }}
        >
          Sign out
        </button>
      </header>

      <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">CV (PDF)</span>
          <input
            type="file"
            accept=".pdf,application/pdf"
            onChange={(e) => {
              setFile(e.target.files?.[0] ?? null);
              setScore(null);
            }}
            required
            className="rounded border border-gray-300 px-3 py-2 text-sm"
          />
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">Job description</span>
          <textarea
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            required
            rows={8}
            placeholder="Paste the job description here."
            className="rounded border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2"
            style={{ outlineColor: "var(--primary)" }}
          />
        </label>
        {error && (
          <p className="text-sm" style={{ color: "var(--weak)" }}>
            {error}
          </p>
        )}
        <button
          type="submit"
          disabled={busy || !file}
          className="rounded px-4 py-2 font-medium text-white disabled:opacity-50"
          style={{ background: "var(--primary)" }}
        >
          {busy ? "Uploading..." : "Upload CV"}
        </button>
      </form>

      {result && (
        <section className="mt-8">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold" style={{ color: "var(--ink)" }}>
              Extracted CV text
            </h2>
            <button
              type="button"
              onClick={handleScore}
              disabled={scoring}
              className="rounded px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
              style={{ background: "var(--primary)" }}
            >
              {scoring ? "Scoring..." : "Score"}
            </button>
          </div>
          {!score && (
            <pre
              className="mt-2 max-h-96 overflow-auto whitespace-pre-wrap rounded border border-gray-200 bg-gray-50 p-4 text-sm"
              style={{ color: "var(--ink)" }}
            >
              {result.cv_text}
            </pre>
          )}
        </section>
      )}

      {score && <ScoreResultView result={score} cvText={result?.cv_text ?? ""} />}
    </main>
  );
}