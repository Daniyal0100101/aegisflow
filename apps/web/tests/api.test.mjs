import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import ts from "typescript";

// Exercise the shipped client without a backend, credentials, or network calls.
const source = await readFile(new URL("../lib/api.ts", import.meta.url), "utf8");
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 },
});
const moduleUrl = `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`;
const originalApiUrl = process.env.NEXT_PUBLIC_API_URL;
let api, configuredApi;
const apiUrl = "http://127.0.0.1:8000";
const configuredApiUrl = "http://127.0.0.1:9000";
try {
  delete process.env.NEXT_PUBLIC_API_URL;
  ({ api } = await import(`${moduleUrl}#default`));
  process.env.NEXT_PUBLIC_API_URL = configuredApiUrl;
  ({ api: configuredApi } = await import(`${moduleUrl}#configured`));
} finally {
  if (originalApiUrl === undefined) delete process.env.NEXT_PUBLIC_API_URL;
  else process.env.NEXT_PUBLIC_API_URL = originalApiUrl;
}

// Mock data uses the existing SessionSnapshot/SimulationState fields, not a new contract.
function snapshot(domain = "disaster", directive = null) {
  return {
    session_id: "test-session",
    domain,
    scenario_name: "Test scenario",
    case_data: {},
    events: [],
    active_directive: directive,
    safety_flags: [],
    next_action: "Monitor general conditions",
    simulation_state: {
      domain,
      scenario_id: domain,
      status_summary: "Test state",
      stability_score: 25,
      risk_level: "critical",
      metrics: {},
      interventions_done: [],
      decisions_applied: [],
      pending_actions: [],
      latest_change: "Initial",
      state_outcome: "Unchanged",
      timeline: [],
    },
  };
}

function mockFetch(t, response) {
  const fetch = t.mock.method(globalThis, "fetch", async () => response);
  t.after(() => fetch.mock.restore());
  return fetch;
}

test("reachability uses the existing root endpoint without caching", async (t) => {
  const fetch = mockFetch(t, new Response("{}"));
  assert.equal(await api.isBackendReachable(), true);
  assert.deepEqual(fetch.mock.calls[0].arguments, [
    `${apiUrl}/`, { method: "GET", cache: "no-store" },
  ]);
});

test("reachability reports unsuccessful HTTP responses as offline", async (t) => {
  mockFetch(t, new Response("unavailable", { status: 503 }));
  assert.equal(await api.isBackendReachable(), false);
});

test("the configured API origin is used without an invented /api prefix", async (t) => {
  const fetch = mockFetch(t, Response.json(snapshot()));
  await configuredApi.startSession("disaster");
  assert.equal(fetch.mock.calls[0].arguments[0], `${configuredApiUrl}/session/start`);
});

test("reachability reports network failures as offline", async (t) => {
  const fetch = t.mock.method(globalThis, "fetch", async () => {
    throw new TypeError("test network failure");
  });
  t.after(() => fetch.mock.restore());
  assert.equal(await api.isBackendReachable(), false);
});

for (const domain of ["clinical", "disaster", "logistics"]) {
  test(`startSession sends ${domain} and returns the complete snapshot`, async (t) => {
    const response = snapshot(domain);
    const fetch = mockFetch(t, Response.json(response));
    assert.deepEqual(await api.startSession(domain), response);
    assert.deepEqual(fetch.mock.calls[0].arguments, [
      `${apiUrl}/session/start`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain }),
      },
    ]);
  });
}

test("applyOverride sends directive, not an invented override action contract", async (t) => {
  const directive = "Hold inventory dispatch";
  const response = snapshot("logistics", directive);
  const fetch = mockFetch(t, Response.json(response));
  assert.deepEqual(await api.applyOverride("test-session", directive), response);
  assert.deepEqual(fetch.mock.calls[0].arguments, [
    `${apiUrl}/session/test-session/override`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ directive }),
    },
  ]);
});

test("JSON API errors retain the status and backend detail", async (t) => {
  mockFetch(t, Response.json({ detail: "Unsupported domain: invalid" }, { status: 400 }));
  await assert.rejects(api.startSession("invalid"), {
    message: "API Error (400): Unsupported domain: invalid",
  });
});

test("non-JSON API errors retain the status and response text", async (t) => {
  mockFetch(t, new Response("Unavailable", { status: 503 }));
  await assert.rejects(api.applyOverride("test-session", "Hold"), {
    message: "API Error (503): Unavailable",
  });
});

test("empty HTTP errors reject rather than returning a null snapshot", async (t) => {
  mockFetch(t, new Response(null, { status: 503 }));
  await assert.rejects(api.startSession("disaster"), {
    message: "API Error (503): ",
  });
});

test("FastAPI validation errors retain their structured details", async (t) => {
  const error = { detail: [{ loc: ["body", "directive"], msg: "Field required", type: "missing" }] };
  mockFetch(t, Response.json(error, { status: 422 }));
  await assert.rejects(api.applyOverride("test-session", "Hold"), {
    message: `API Error (422): ${JSON.stringify(error)}`,
  });
});

for (const [name, response] of [
  ["non-JSON", () => new Response("not a snapshot")],
  ["empty", () => new Response(null, { status: 204 })],
]) {
  test(`${name} successful responses reject instead of inventing a snapshot`, async (t) => {
    mockFetch(t, response());
    await assert.rejects(api.startSession("disaster"), SyntaxError);
  });
}
