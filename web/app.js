// 화면 상태와 렌더링. 사용자 입력은 항상 textContent로 넣는다(innerHTML 금지).
import { api, ApiError, createMeal, tokenStore } from "./api.js";

const $ = (sel) => document.querySelector(sel);

const MEAL_TYPES = { breakfast: "아침", lunch: "점심", dinner: "저녁", snack: "간식" };
const PORTIONS = { small: "적게", medium: "보통", large: "많이" };
const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

const state = {
  user: null,     // { id, email, timezone, created_at }
  tab: "log",
  date: null,     // 보고 있는 날짜 YYYY-MM-DD
  editingId: null,
  weekStart: null,
};

// ---- 날짜 (사용자 시간대 기준) --------------------------------------------
function todayIn(timeZone) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone, year: "numeric", month: "2-digit", day: "2-digit",
  }).format(new Date());
}
const today = () => todayIn(state.user.timezone);
const parse = (iso) => new Date(`${iso}T00:00:00Z`);
function addDays(iso, n) {
  const d = parse(iso);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}
function mondayOf(iso) {
  return addDays(iso, -((parse(iso).getUTCDay() + 6) % 7));
}
function shortDate(iso) {
  const d = parse(iso);
  return `${d.getUTCMonth() + 1}월 ${d.getUTCDate()}일`;
}
function dateLabel(iso) {
  const t = today();
  const wd = WEEKDAYS[parse(iso).getUTCDay()];
  if (iso === t) return `오늘 · ${shortDate(iso)} (${wd})`;
  if (iso === addDays(t, -1)) return `어제 · ${shortDate(iso)} (${wd})`;
  return `${shortDate(iso)} (${wd})`;
}
const browserTimeZone = () => Intl.DateTimeFormat().resolvedOptions().timeZone;

// ---- 공통 UI ---------------------------------------------------------------
function el(tag, props = {}, ...children) {
  const node = Object.assign(document.createElement(tag), props);
  for (const c of children) if (c != null) node.append(c);
  return node;
}

let toastTimer;
function toast(message) {
  const t = $("#toast");
  t.textContent = message;
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, 3000);
}

function errorMessage(err) {
  if (!(err instanceof ApiError)) return "연결이 불안정해요. 잠시 후 다시 시도해 주세요.";
  const field = err.details[0]?.field;
  const reason = err.details[0]?.reason;
  if (err.code === "invalid_credentials") return "이메일 또는 비밀번호가 맞지 않아요.";
  if (err.status === 403) return "비밀번호가 맞지 않아요.";
  if (err.status === 409) return "이미 사용 중인 이메일이에요.";
  if (field === "description") return "먹은 것을 200자 안으로 적어 주세요.";
  if (field === "meal_date" && reason === "future_date") return "아직 오지 않은 날짜에는 기록할 수 없어요.";
  if (field === "email") return "이메일 형식을 확인해 주세요.";
  if (field === "password") return "비밀번호는 8자 이상이어야 해요.";
  if (field === "memo") return "메모는 500자 안으로 적어 주세요.";
  return "요청을 처리하지 못했어요. 잠시 후 다시 시도해 주세요.";
}

// 로그인이 풀렸으면 첫 화면으로, 그 밖의 오류는 안내만 한다.
async function guard(fn) {
  try {
    return await fn();
  } catch (err) {
    if (err instanceof ApiError && err.status === 401 && state.user) {
      signOutLocally("다시 로그인해 주세요.");
      return undefined;
    }
    toast(errorMessage(err));
    return undefined;
  }
}

// ---- 화면 전환 ---------------------------------------------------------------
function showOnboarding() {
  $("#app").hidden = true;
  $("#onboarding").hidden = false;
}

async function enterApp(user) {
  state.user = user;
  state.date = today();
  state.weekStart = mondayOf(state.date);
  $("#onboarding").hidden = true;
  $("#app").hidden = false;
  await showTab("log");
}

function signOutLocally(message) {
  tokenStore.clear();
  state.user = null;
  resetForm();
  showOnboarding();
  if (message) toast(message);
}

async function showTab(tab) {
  state.tab = tab;
  for (const b of document.querySelectorAll(".tab")) {
    if (b.dataset.tab === tab) b.setAttribute("aria-current", "page");
    else b.removeAttribute("aria-current");
  }
  for (const name of ["log", "week", "settings"]) $(`#tab-${name}`).hidden = name !== tab;
  if (tab === "log") await renderLog();
  if (tab === "week") await renderWeek();
  if (tab === "settings") renderSettings();
}

// ---- 기록 탭 -----------------------------------------------------------------
function chipGroup(name) {
  return $(`.chips[data-group="${name}"]`);
}
function selected(name) {
  return chipGroup(name).querySelector('[aria-pressed="true"]')?.dataset.value ?? null;
}
function select(name, value) {
  for (const c of chipGroup(name).querySelectorAll(".chip")) {
    c.setAttribute("aria-pressed", String(c.dataset.value === value));
  }
}

function resetForm() {
  state.editingId = null;
  $("#description").value = "";
  $("#memo").value = "";
  $("#memo-box").open = false;
  select("meal_type", null);
  select("portion", null);
  $("#form-title").textContent = "무엇을 먹었나요?";
  $("#save").textContent = "기록하기";
  $("#cancel-edit").hidden = true;
}

function startEdit(meal) {
  state.editingId = meal.id;
  $("#description").value = meal.description;
  $("#memo").value = meal.memo ?? "";
  $("#memo-box").open = Boolean(meal.memo);
  select("meal_type", meal.meal_type);
  select("portion", meal.portion);
  $("#form-title").textContent = "기록 고치기";
  $("#save").textContent = "저장하기";
  $("#cancel-edit").hidden = false;
  $("#description").focus();
}

function renderMeal(meal) {
  const meta = [MEAL_TYPES[meal.meal_type], PORTIONS[meal.portion]].filter(Boolean).join(" · ");
  const edit = el("button", { type: "button", textContent: "수정", className: "link" });
  const del = el("button", { type: "button", textContent: "삭제", className: "link" });
  edit.setAttribute("aria-label", `${meal.description} 수정`);
  del.setAttribute("aria-label", `${meal.description} 삭제`);
  edit.addEventListener("click", () => startEdit(meal));
  del.addEventListener("click", () => deleteMeal(meal));
  return el(
    "li",
    { className: "meal" },
    el(
      "div",
      { className: "meal-body" },
      el("p", { className: "meal-desc", textContent: meal.description }),
      meta ? el("p", { className: "meal-meta", textContent: meta }) : null,
      meal.memo ? el("p", { className: "meal-memo", textContent: meal.memo }) : null,
    ),
    el("div", { className: "meal-actions" }, edit, del),
  );
}

async function renderLog() {
  const t = today();
  $("#date-label").textContent = dateLabel(state.date);
  $("#next-day").disabled = state.date >= t;
  $("#go-today").hidden = state.date === t;

  const [list, recent] = await Promise.all([
    guard(() => api(`/v1/meals?date=${state.date}`)),
    guard(() => api("/v1/meals/recent-descriptions")),
  ]);
  if (!list) return;

  const ul = $("#meal-list");
  ul.replaceChildren(...list.items.map(renderMeal));
  if (list.items.length === 0) {
    ul.append(el("li", { className: "empty", textContent: "아직 기록이 없어요. 생각나는 것 하나만 적어도 충분해요." }));
  }

  const box = $("#recent");
  box.replaceChildren(
    ...(recent?.items ?? []).map((text) => {
      const chip = el("button", { type: "button", className: "chip recent", textContent: text });
      chip.addEventListener("click", () => {
        $("#description").value = text;
        $("#save").focus();
      });
      return chip;
    }),
  );
  box.hidden = box.childElementCount === 0;
}

async function saveMeal(event) {
  event.preventDefault();
  const description = $("#description").value.trim();
  if (!description) {
    toast("먹은 것을 한 줄만 적어 주세요.");
    $("#description").focus();
    return;
  }
  const fields = {
    description,
    meal_type: selected("meal_type"),
    portion: selected("portion"),
    memo: $("#memo").value.trim() || null,
  };
  const button = $("#save");
  button.disabled = true;
  const ok = await guard(async () => {
    if (state.editingId) {
      await api(`/v1/meals/${state.editingId}`, { method: "PATCH", body: fields });
    } else {
      // 선택하지 않은 항목은 보내지 않는다(서버 기본값 사용).
      const body = Object.fromEntries(Object.entries(fields).filter(([, v]) => v !== null));
      await createMeal({ ...body, meal_date: state.date });
    }
    return true;
  });
  button.disabled = false;
  if (!ok) return;
  toast(state.editingId ? "고쳤어요." : "기록했어요.");
  resetForm();
  await renderLog();
}

async function deleteMeal(meal) {
  if (!confirm(`"${meal.description}" 기록을 지울까요?`)) return;
  const ok = await guard(async () => {
    await api(`/v1/meals/${meal.id}`, { method: "DELETE" });
    return true;
  });
  if (!ok) return;
  if (state.editingId === meal.id) resetForm();
  toast("지웠어요.");
  await renderLog();
}

async function moveDay(n) {
  const next = addDays(state.date, n);
  if (next > today()) return;
  state.date = next;
  resetForm();
  await renderLog();
}

// ---- 한 주 탭 ------------------------------------------------------------------
async function renderWeek() {
  const start = state.weekStart;
  const end = addDays(start, 6);
  $("#week-label").textContent = `${shortDate(start)} – ${shortDate(end)}`;
  $("#next-week").disabled = addDays(start, 7) > today();

  const s = await guard(() => api(`/v1/summaries/weekly?start=${start}`));
  if (!s) return;
  // 기록하지 않은 날을 실패로 보이게 하지 않는다(PRD 원칙 4).
  $("#week-headline").textContent = s.days_logged > 0
    ? `이 주에 ${s.days_logged}일 기록했어요`
    : "이 주는 아직 기록이 없어요. 지난 날짜도 언제든 적을 수 있어요.";

  const t = today();
  $("#week-days").replaceChildren(
    ...s.daily_counts.map(({ date, count }) => {
      const b = el(
        "button",
        { type: "button", className: count > 0 ? "day logged" : "day" },
        el("span", { className: "wd", textContent: WEEKDAYS[parse(date).getUTCDay()] }),
        el("span", { className: "dd", textContent: String(parse(date).getUTCDate()) }),
        el("span", { className: "cnt", textContent: count > 0 ? `${count}건` : "" }),
      );
      b.setAttribute("aria-label", `${shortDate(date)} ${count > 0 ? `${count}건 기록` : "기록 없음"}`);
      b.disabled = date > t;
      b.addEventListener("click", async () => {
        state.date = date;
        resetForm();
        await showTab("log");
      });
      return el("li", {}, b);
    }),
  );

  const p = s.portion_counts;
  $("#week-portions").textContent = s.days_logged > 0
    ? `식사량: 적게 ${p.small} · 보통 ${p.medium} · 많이 ${p.large} · 고르지 않음 ${p.none}`
    : "";
}

async function moveWeek(n) {
  const next = addDays(state.weekStart, 7 * n);
  if (next > today()) return;
  state.weekStart = next;
  await renderWeek();
}

// ---- 설정 탭 -------------------------------------------------------------------
function renderSettings() {
  const { email, timezone } = state.user;
  $("#account-anonymous").hidden = email !== null;
  $("#account-linked").hidden = email === null;
  $("#account-email").textContent = email ?? "";
  $("#timezone").textContent = timezone;
  $("#sync-timezone").hidden = timezone === browserTimeZone();
  $("#delete-password-row").hidden = email === null;
}

async function linkAccount(event) {
  event.preventDefault();
  const user = await guard(() => api("/v1/auth/link", {
    method: "POST",
    body: { email: $("#link-email").value, password: $("#link-password").value },
  }));
  if (!user) return;
  state.user = user;
  $("#link-form").reset();
  toast("계정을 연결했어요. 이제 다른 기기에서도 로그인할 수 있어요.");
  renderSettings();
}

async function syncTimezone() {
  const user = await guard(() => api("/v1/me", { method: "PATCH", body: { timezone: browserTimeZone() } }));
  if (!user) return;
  state.user = user;
  state.date = today();
  state.weekStart = mondayOf(state.date);
  toast("시간대를 바꿨어요.");
  renderSettings();
}

async function logout() {
  if (state.user.email === null
    && !confirm("계정을 연결하지 않으면 로그아웃 후 지금까지의 기록을 다시 볼 수 없어요. 그래도 로그아웃할까요?")) {
    return;
  }
  await guard(() => api("/v1/auth/logout", { method: "POST" }));
  signOutLocally("로그아웃했어요.");
}

async function deleteAccount(event) {
  event.preventDefault();
  if (!confirm("계정과 모든 기록을 지금 삭제할까요? 되돌릴 수 없어요.")) return;
  const body = state.user.email === null ? undefined : { password: $("#delete-password").value };
  const ok = await guard(async () => {
    await api("/v1/me", { method: "DELETE", body });
    return true;
  });
  if (!ok) return;
  $("#delete-form").reset();
  signOutLocally("탈퇴했어요. 모든 기록을 삭제했어요.");
}

// ---- 첫 화면 -------------------------------------------------------------------
async function startAnonymous() {
  const data = await guard(() => api("/v1/auth/anonymous", {
    method: "POST",
    body: { privacy_consent: true, timezone: browserTimeZone() },
  }));
  if (!data) return;
  tokenStore.set(data.access_token);
  await enterApp(data.user);
}

async function login(event) {
  event.preventDefault();
  const data = await guard(() => api("/v1/auth/login", {
    method: "POST",
    body: { email: $("#login-email").value, password: $("#login-password").value },
  }));
  if (!data) return;
  tokenStore.set(data.access_token);
  $("#login-form").reset();
  await enterApp(data.user);
}

// ---- 시작 ----------------------------------------------------------------------
function bind() {
  $("#consent").addEventListener("change", (e) => { $("#start-anonymous").disabled = !e.target.checked; });
  $("#start-anonymous").addEventListener("click", startAnonymous);
  $("#login-form").addEventListener("submit", login);

  for (const b of document.querySelectorAll(".tab")) b.addEventListener("click", () => showTab(b.dataset.tab));

  for (const group of document.querySelectorAll(".chips[data-group]")) {
    group.addEventListener("click", (e) => {
      const chip = e.target.closest(".chip");
      if (!chip) return;
      // 같은 칩을 다시 누르면 선택 해제
      select(group.dataset.group, chip.getAttribute("aria-pressed") === "true" ? null : chip.dataset.value);
    });
  }
  $("#meal-form").addEventListener("submit", saveMeal);
  $("#cancel-edit").addEventListener("click", resetForm);
  $("#prev-day").addEventListener("click", () => moveDay(-1));
  $("#next-day").addEventListener("click", () => moveDay(1));
  $("#go-today").addEventListener("click", async () => {
    state.date = today();
    resetForm();
    await renderLog();
  });
  $("#prev-week").addEventListener("click", () => moveWeek(-1));
  $("#next-week").addEventListener("click", () => moveWeek(1));

  $("#link-form").addEventListener("submit", linkAccount);
  $("#sync-timezone").addEventListener("click", syncTimezone);
  $("#logout").addEventListener("click", logout);
  $("#delete-form").addEventListener("submit", deleteAccount);
}

async function boot() {
  bind();
  if (!tokenStore.get()) {
    showOnboarding();
    return;
  }
  try {
    await enterApp(await api("/v1/me"));
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) signOutLocally();
    else {
      showOnboarding();
      toast(errorMessage(err));
    }
  }
}

boot();
