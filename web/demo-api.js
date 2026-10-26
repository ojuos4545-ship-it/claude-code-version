// 체험 모드: 서버 없이 브라우저 저장소만으로 백엔드 API를 흉내 낸다.
// 화면 확인용이다. 응답 형식과 주요 검증은 backend/와 맞추지만 보안 기능(요청 수 제한,
// 비밀번호 해시 강도 등)은 흉내 내지 않는다. 실제 서비스에서는 쓰지 않는다.

const STORE_KEY = "easy-meal-log.demo";
const MEAL_TYPE_ORDER = ["breakfast", "lunch", "dinner", "snack"];
const MEAL_TYPES = new Set(MEAL_TYPE_ORDER);
const PORTIONS = new Set(["small", "medium", "large"]);
const CONTROL = /[\u0000-\u001f\u007f]/u;

let memory = null; // 저장소를 쓸 수 없는 환경(사생활 보호 창 등)에서의 대체 저장

function load() {
  if (memory) return memory;
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (raw) return JSON.parse(raw);
  } catch { /* 아래 기본값 */ }
  return { users: {}, sessions: {}, meals: {} };
}

function save(db) {
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify(db));
    memory = null;
  } catch {
    memory = db;
  }
}

const ok = (status, data = null) => ({ status, data });
function fail(status, code, message, field, reason) {
  const details = field ? [{ field, reason, message }] : [];
  return { status, data: { error: { code, message, details } } };
}
const invalid = (field, reason, message) => fail(422, "validation_error", message, field, reason);

const now = () => new Date().toISOString();
const id = () => crypto.randomUUID().replaceAll("-", "");
const length = (s) => [...s].length; // 서버와 같이 코드포인트 기준

function todayIn(timeZone) {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-US", { timeZone, year: "numeric", month: "2-digit", day: "2-digit" })
      .formatToParts(new Date())
      .map((p) => [p.type, p.value]),
  );
  return `${parts.year}-${parts.month}-${parts.day}`;
}
function addDays(iso, n) {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}
const isDate = (s) => typeof s === "string" && /^\d{4}-\d{2}-\d{2}$/.test(s)
  && !Number.isNaN(Date.parse(`${s}T00:00:00Z`)) && new Date(`${s}T00:00:00Z`).toISOString().startsWith(s);

async function hash(password) {
  const bytes = new TextEncoder().encode(`easy-meal-log-demo:${password}`);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function userOut(u) {
  return { id: u.id, email: u.email, timezone: u.timezone, created_at: u.created_at };
}
function mealOut(m) {
  const { user_id: _, idempotency_key: __, ...rest } = m;
  return rest;
}
function issue(db, user) {
  const token = id() + id();
  db.sessions[token] = user.id;
  return { access_token: token, token_type: "bearer", expires_at: addDays(now().slice(0, 10), 30), user: userOut(user) };
}
function validTimeZone(tz) {
  try { new Intl.DateTimeFormat("en-US", { timeZone: tz }); return true; } catch { return false; }
}

function checkDescription(value) {
  if (typeof value !== "string" || !value.trim()) return invalid("description", "value_error", "must not be empty or whitespace only");
  if (length(value.trim()) > 200) return invalid("description", "value_error", "must be at most 200 characters");
  if (CONTROL.test(value.trim())) return invalid("description", "value_error", "must be a single line without control characters");
  return null;
}
function checkOptional(body) {
  if (body.meal_type != null && !MEAL_TYPES.has(body.meal_type)) return invalid("meal_type", "enum", "invalid meal_type");
  if (body.portion != null && !PORTIONS.has(body.portion)) return invalid("portion", "enum", "invalid portion");
  if (body.memo != null && length(String(body.memo).trim()) > 500) return invalid("memo", "value_error", "must be at most 500 characters");
  return null;
}
function sortMeals(list) {
  const order = (t) => (t ? MEAL_TYPE_ORDER.indexOf(t) : MEAL_TYPE_ORDER.length);
  return list.sort((a, b) => a.meal_date.localeCompare(b.meal_date)
    || order(a.meal_type) - order(b.meal_type)
    || a.created_at.localeCompare(b.created_at));
}

// fetch와 같은 결과 모양 { status, data }를 돌려준다.
export async function demoRequest(method, path, body, headers) {
  const db = load();
  const url = new URL(path, "http://demo.local");
  const route = `${method} ${url.pathname}`;
  const token = (headers.Authorization ?? "").replace(/^Bearer /, "");
  const user = db.users[db.sessions[token]];

  if (route === "POST /v1/auth/anonymous") {
    if (body?.privacy_consent !== true) return invalid("privacy_consent", "literal_error", "consent required");
    const tz = body.timezone ?? "Asia/Seoul";
    if (!validTimeZone(tz)) return invalid("timezone", "invalid", "unknown IANA time zone");
    const u = { id: id(), email: null, password_hash: null, timezone: tz, created_at: now() };
    db.users[u.id] = u;
    const out = issue(db, u);
    save(db);
    return ok(201, out);
  }
  if (route === "POST /v1/auth/login") {
    const email = String(body?.email ?? "").trim().toLowerCase();
    const found = Object.values(db.users).find((u) => u.email === email);
    if (!found || found.password_hash !== await hash(String(body?.password ?? ""))) {
      return fail(401, "invalid_credentials", "Email or password is incorrect.");
    }
    const out = issue(db, found);
    save(db);
    return ok(200, out);
  }

  if (!user) return fail(401, "unauthenticated", "Authentication required.");

  if (route === "POST /v1/auth/link") {
    const email = String(body?.email ?? "").trim().toLowerCase();
    const password = String(body?.password ?? "");
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return invalid("email", "value_error", "must be a valid email address");
    if (password.length < 8 || password.length > 128) return invalid("password", "string_too_short", "must be 8 to 128 characters");
    if (user.email) return fail(409, "conflict", "An email login is already linked.", "email", "already_linked");
    if (Object.values(db.users).some((u) => u.email === email)) {
      return fail(409, "conflict", "Email is already registered.", "email", "already_registered");
    }
    user.email = email;
    user.password_hash = await hash(password);
    save(db);
    return ok(200, userOut(user));
  }
  if (route === "POST /v1/auth/logout") {
    delete db.sessions[token];
    save(db);
    return ok(204);
  }
  if (route === "GET /v1/me") return ok(200, userOut(user));
  if (route === "PATCH /v1/me") {
    if (!validTimeZone(body?.timezone)) return invalid("timezone", "invalid", "unknown IANA time zone");
    user.timezone = body.timezone;
    save(db);
    return ok(200, userOut(user));
  }
  if (route === "DELETE /v1/me") {
    if (user.email && user.password_hash !== await hash(String(body?.password ?? ""))) {
      return fail(403, "forbidden", "Password confirmation failed.");
    }
    for (const [t, uid] of Object.entries(db.sessions)) if (uid === user.id) delete db.sessions[t];
    for (const [mid, m] of Object.entries(db.meals)) if (m.user_id === user.id) delete db.meals[mid];
    delete db.users[user.id];
    save(db);
    return ok(204);
  }

  const mine = () => Object.values(db.meals).filter((m) => m.user_id === user.id);
  const today = todayIn(user.timezone);

  if (route === "POST /v1/meals") {
    const err = checkDescription(body?.description) ?? checkOptional(body ?? {});
    if (err) return err;
    const mealDate = body.meal_date ?? today;
    if (!isDate(mealDate)) return invalid("meal_date", "date_from_datetime_parsing", "invalid date");
    if (mealDate > today) return invalid("meal_date", "future_date", "meal_date must not be later than today");
    const key = headers["Idempotency-Key"];
    const replay = key && mine().find((m) => m.idempotency_key === key);
    if (replay) return ok(200, mealOut(replay));
    const t = now();
    const meal = {
      id: id(), user_id: user.id, description: body.description.trim(), meal_date: mealDate,
      meal_type: body.meal_type ?? null, portion: body.portion ?? null,
      memo: body.memo?.trim() || null, created_at: t, updated_at: t, idempotency_key: key ?? null,
    };
    db.meals[meal.id] = meal;
    save(db);
    return ok(201, mealOut(meal));
  }
  if (route === "GET /v1/meals") {
    const date = url.searchParams.get("date");
    if (!isDate(date)) return invalid("date", "invalid", "invalid date");
    const items = sortMeals(mine().filter((m) => m.meal_date === date)).map(mealOut);
    return ok(200, { items, next_offset: null });
  }
  if (route === "GET /v1/meals/recent-descriptions") {
    const since = new Date(Date.now() - 30 * 86400000).toISOString();
    const seen = new Set();
    const items = [];
    for (const m of mine().sort((a, b) => b.created_at.localeCompare(a.created_at))) {
      if (m.created_at < since || seen.has(m.description)) continue;
      seen.add(m.description);
      items.push(m.description);
      if (items.length === 10) break;
    }
    return ok(200, { items });
  }
  if (route === "GET /v1/summaries/weekly") {
    const start = url.searchParams.get("start");
    if (!isDate(start)) return invalid("start", "invalid", "invalid date");
    const days = Array.from({ length: 7 }, (_, i) => addDays(start, i));
    const inRange = mine().filter((m) => m.meal_date >= days[0] && m.meal_date <= days[6]);
    const portions = { small: 0, medium: 0, large: 0, none: 0 };
    for (const m of inRange) portions[m.portion ?? "none"] += 1;
    const daily = days.map((date) => ({ date, count: inRange.filter((m) => m.meal_date === date).length }));
    return ok(200, {
      start: days[0], end: days[6],
      days_logged: daily.filter((d) => d.count > 0).length,
      daily_counts: daily, portion_counts: portions,
    });
  }

  const match = url.pathname.match(/^\/v1\/meals\/([0-9a-f]+)$/);
  const meal = match && db.meals[match[1]];
  if (match && (!meal || meal.user_id !== user.id)) return fail(404, "not_found", "Resource not found.");
  if (match && method === "GET") return ok(200, mealOut(meal));
  if (match && method === "DELETE") {
    delete db.meals[meal.id];
    save(db);
    return ok(204);
  }
  if (match && method === "PATCH") {
    if ("description" in body) {
      const err = checkDescription(body.description);
      if (err) return err;
    }
    const err = checkOptional(body);
    if (err) return err;
    for (const k of ["description", "meal_type", "portion", "memo"]) {
      if (k in body) meal[k] = typeof body[k] === "string" ? body[k].trim() || null : body[k];
    }
    meal.updated_at = now();
    save(db);
    return ok(200, mealOut(meal));
  }
  return fail(404, "not_found", "Resource not found.");
}
