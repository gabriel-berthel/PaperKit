
export async function request(url, {
  method = "GET",
  payload = null
} = {}) {
  const res = await fetch(url, {
    method,
    headers: payload ? { "Content-Type": "application/json" } : undefined,
    body: payload ? JSON.stringify(payload) : undefined
  });

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }

  return await res.json();
}

export const ENDPOINTS = {
  SIMPLIFY: "http://127.0.0.1:8080/api/simplify",
  SUMMARIZE: "http://127.0.0.1:8080/api/summarize",
  WHAT_IS_IT: "http://127.0.0.1:8080/api/whatItIs",
  GLINER_PROBE: "http://127.0.0.1:8080/api/entity/probe",
  PIPER: 'http://localhost:8080/api/tts'
}