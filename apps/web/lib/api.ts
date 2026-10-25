import type { SessionSnapshot } from "../types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const handleResponse = async (res: Response): Promise<SessionSnapshot> => {
  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try {
      const data = JSON.parse(text);
      detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data);
    } catch {
      // Non-JSON errors (for example, a proxy failure) still retain their status.
    }
    throw new Error(`API Error (${res.status}): ${detail}`);
  }
  return res.json();
};

export const api = {
  isBackendReachable: async (): Promise<boolean> => {
    try {
      const res = await fetch(`${API_URL}/`, {
        method: "GET",
        cache: "no-store",
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  startSession: async (domain: string): Promise<SessionSnapshot> => {
    const res = await fetch(`${API_URL}/session/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ domain }),
    });
    return handleResponse(res);
  },

  applyOverride: async (sessionId: string, directive: string): Promise<SessionSnapshot> => {
    const res = await fetch(`${API_URL}/session/${sessionId}/override`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ directive }),
    });
    return handleResponse(res);
  },
};
