"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { createSession } from "./api";
import { setUserId } from "./session";

export default function LoginPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const userId = await createSession(name);
      setUserId(userId);
      router.push("/app");
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <h1 className="text-3xl font-bold" style={{ color: "var(--ink)" }}>
        JobFit
      </h1>
      <p className="mt-2" style={{ color: "var(--muted)" }}>
        Sign in to start comparing your CV against a job description.
      </p>
      <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">Your name</span>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="rounded border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2"
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
          disabled={busy}
          className="rounded px-4 py-2 font-medium text-white disabled:opacity-50"
          style={{ background: "var(--primary)" }}
        >
          {busy ? "Signing in..." : "Enter"}
        </button>
      </form>
    </main>
  );
}