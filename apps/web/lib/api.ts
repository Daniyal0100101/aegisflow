import type { SessionSnapshot } from "../types";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

/** Read a snapshot or reject with the backend's HTTP status and error detail. */
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
  /** Check backend availability without starting a session or caching a stale result. */
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

  /** Start a simulation in the requested domain and return its initial snapshot. */
  startSession: async (domain: string): Promise<SessionSnapshot> => {
    const res = await fetch(`${API_URL}/session/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ domain }),
    });
    return handleResponse(res);
  },

  /** Apply a directive to an existing session and return the updated snapshot. */
  applyOverride: async (sessionId: string, directive: string): Promise<SessionSnapshot> => {
    const res = await fetch(`${API_URL}/session/${sessionId}/override`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ directive }),
    });
    return handleResponse(res);
  },
};
