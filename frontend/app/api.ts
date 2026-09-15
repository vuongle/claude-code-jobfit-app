/** Thin wrappers around the JobFit API. All endpoints share the origin that serves this app. */

export async function createSession(name: string): Promise<number> {
  const body = new FormData();
  body.set("name", name);
  const response = await fetch("/api/session", { method: "POST", body });
  if (!response.ok) throw new Error(`Session failed (${response.status})`);
  const data = (await response.json()) as { user_id: number };
  return data.user_id;
}

export interface UploadResult {
  id: number;
  filename: string;
  cv_text: string;
}

export async function uploadCv(
  userId: number,
  file: File,
  jdText: string,
): Promise<UploadResult> {
  const body = new FormData();
  body.set("user_id", String(userId));
  body.set("jd_text", jdText);
  body.set("cv_file", file);
  const response = await fetch("/api/uploads", { method: "POST", body });
  if (!response.ok) {
    const detail = await response
      .json()
      .then((data) => data.detail)
      .catch(() => null);
    throw new Error(typeof detail === "string" ? detail : `Upload failed (${response.status})`);
  }
  return (await response.json()) as UploadResult;
}