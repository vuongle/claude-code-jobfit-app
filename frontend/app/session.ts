/** Fake-session helpers: the user id comes from POST /api/session and lives in localStorage. */

export function getUserId(): number | null {
  const raw = localStorage.getItem("jobfit_user_id");
  if (raw === null) return null;
  const id = Number(raw);
  return Number.isInteger(id) && id > 0 ? id : null;
}

export function setUserId(id: number): void {
  localStorage.setItem("jobfit_user_id", String(id));
}

export function clearUserId(): void {
  localStorage.removeItem("jobfit_user_id");
}