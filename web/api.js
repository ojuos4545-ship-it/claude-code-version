// API 호출과 토큰 보관. 토큰은 Authorization 헤더로만 보낸다(쿠키 없음).
import { config } from "./config.js";

const TOKEN_KEY = "easy-meal-log.token";

export const tokenStore = {
  get() {
    try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
  },
  set(token) {
    try { localStorage.setItem(TOKEN_KEY, token); } catch { /* 저장 불가 환경: 이번 탭에서만 유지 */ }
  },
  clear() {
    try { localStorage.removeItem(TOKEN_KEY); } catch { /* 무시 */ }
  },
};

export class ApiError extends Error {
  constructor(status, body) {
    super(body?.error?.message ?? `HTTP ${status}`);
    this.status = status;
    this.code = body?.error?.code;
    this.details = body?.error?.details ?? [];
  }
}

export async function api(path, { method = "GET", body, headers = {} } = {}) {
  const h = { ...headers };
  if (body !== undefined) h["Content-Type"] = "application/json";
  const token = tokenStore.get();
  if (token) h.Authorization = `Bearer ${token}`;

  if (config.demo) {
    // 체험 모드: 서버 대신 브라우저 저장소로 처리한다(demo-api.js).
    const { demoRequest } = await import("./demo-api.js");
    const { status, data } = await demoRequest(method, path, body, h);
    if (status >= 400) throw new ApiError(status, data);
    return data;
  }

  const res = await fetch(config.apiBase + path, {
    method,
    headers: h,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, data);
  return data;
}

// 기록 생성은 네트워크 오류 시 같은 Idempotency-Key로 한 번 더 보낸다.
// 첫 요청이 서버에 도착했더라도 기록이 두 번 생기지 않는다.
export async function createMeal(meal) {
  const headers = { "Idempotency-Key": crypto.randomUUID() };
  try {
    return await api("/v1/meals", { method: "POST", body: meal, headers });
  } catch (err) {
    if (err instanceof ApiError) throw err;
    return api("/v1/meals", { method: "POST", body: meal, headers });
  }
}
