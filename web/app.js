// 화면 상태와 렌더링. 사용자 입력은 항상 textContent로 넣는다(innerHTML 금지).
import { api, ApiError, createMeal, tokenStore } from "./api.js";
import { config } from "./config.js";

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

// 브라우저 기본 confirm() 대신 화면 안 확인 창을 쓴다.
// claude.ai 같은 iframe 환경에서는 confirm()이 뜨지 않고 항상 false를 돌려준다.
function askConfirm(message, okLabel = "확인") {
  const dialog = $("#confirm-dialog");
  const ok = $("#confirm-ok");
  const cancel = $("#confirm-cancel");
  const opener = document.activeElement;
  $("#confirm-message").textContent = message;
  ok.textContent = okLabel;
  return new Promise((resolve) => {
    function finish(value) {
      ok.removeEventListener("click", onOk);
      cancel.removeEventListener("click", onCancel);
      dialog.removeEventListener("cancel", onEscape);
      dialog.close();
      if (opener instanceof HTMLElement && opener.isConnected) opener.focus();
      resolve(value);
    }
    const onOk = () => finish(true);
    const onCancel = () => finish(false);
    const onEscape = (e) => { e.preventDefault(); finish(false); };
    ok.addEventListener("click", onOk);
    cancel.addEventListener("click", onCancel);
    dialog.addEventListener("cancel", onEscape);
    dialog.showModal();
    cancel.focus(); // 되돌릴 수 없는 동작이 많아 기본 초점은 취소에 둔다
  });
}

let toastTimer;
function toast(message) {
  const t = $("#toast");
  t.textContent = message;
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, 3000);
}

// 오류 안내: 상태 코드만이 아니라 err.code·details와 화면 맥락(context)으로 고른다.
// context: "meal"(기록 저장·삭제), "login", "link"(계정 연결), "delete-account", 그 밖은 생략.
function fieldMessage(field, detail, context) {
  const reason = detail?.reason ?? "";
  const text = detail?.message ?? "";
  const tooLong = /at most|too_long/.test(`${reason} ${text}`);
  const control = /control|single line/.test(text);
  if (field === "description") {
    if (tooLong) return "먹은 것을 200자 안으로 적어 주세요.";
    if (control) return "먹은 것은 탭이나 줄바꿈 없이 한 줄로 적어 주세요.";
    return "먹은 것을 한 줄만 적어 주세요.";
  }
  if (field === "memo") {
    if (control) return "메모에 쓸 수 없는 특수 문자가 있어요. 지우고 다시 저장해 주세요.";
    return "메모는 500자 안으로 적어 주세요.";
  }
  if (field === "meal_date" && reason === "future_date") return "아직 오지 않은 날짜에는 기록할 수 없어요.";
  if (field === "email") return "이메일 형식을 확인해 주세요.";
  if (field === "password") {
    if (reason === "string_too_long") return "비밀번호는 128자 이하로 적어 주세요.";
    if (context === "login") return "이메일 또는 비밀번호가 맞지 않아요.";
    return "비밀번호는 8자 이상이어야 해요.";
  }
  return null;
}

function errorMessage(err, context) {
  if (!(err instanceof ApiError)) return "연결이 불안정해요. 잠시 후 다시 시도해 주세요.";
  if (err.status === 429 || err.code === "rate_limited") return "시도가 많았어요. 잠시 후 다시 시도해 주세요.";
  if (err.status === 503 || err.code === "server_busy") return "지금 요청이 많아요. 잠시 후 다시 시도해 주세요.";
  if (err.code === "https_required") return "보안 연결(HTTPS)이 필요해요. 주소가 https://로 시작하는지 확인해 주세요.";
  if (err.code === "invalid_credentials") return "이메일 또는 비밀번호가 맞지 않아요.";
  if (err.status === 403) {
    return context === "delete-account"
      ? "비밀번호가 맞지 않아요. 확인하고 다시 입력해 주세요."
      : "이 요청을 처리할 수 없어요.";
  }
  if (err.status === 409) {
    const reason = err.details[0]?.reason;
    if (context === "link" && reason === "already_registered") return "이미 다른 계정에서 쓰고 있는 이메일이에요.";
    if (context === "link" && reason === "already_linked") return "이 계정에는 이미 이메일이 연결돼 있어요.";
    return "다른 요청과 겹쳤어요. 화면을 새로 고친 뒤 다시 시도해 주세요.";
  }
  if (err.status === 422) {
    const detail = err.details[0];
    const msg = fieldMessage(detail?.field, detail, context);
    if (msg) return msg;
    return "입력한 내용을 확인해 주세요.";
  }
  if (err.status === 404) return "찾을 수 없어요. 화면을 새로 고쳐 주세요.";
  return "요청을 처리하지 못했어요. 잠시 후 다시 시도해 주세요.";
}

// 로그인이 풀렸으면 첫 화면으로, 그 밖의 오류는 안내만 한다.
async function guard(fn, context) {
  try {
    return await fn();
  } catch (err) {
    if (err instanceof ApiError && err.status === 401 && err.code !== "invalid_credentials" && state.user) {
      signOutLocally("다시 로그인해 주세요.");
      return undefined;
    }
    toast(errorMessage(err, context));
    return undefined;
  }
}

// ---- 화면 전환 ---------------------------------------------------------------
function showScreen(id) {
  for (const name of ["onboarding", "reconnect", "app"]) $(`#${name}`).hidden = name !== id;
}
const showOnboarding = () => showScreen("onboarding");

// 토큰이 있는데 확인하지 못했으면(네트워크 오류, 5xx, 429) 첫 화면을 띄우지 않는다.
// 첫 화면에서 "바로 시작하기"를 누르면 기존 토큰이 새 익명 계정으로 바뀌어 기록을 잃기 때문이다.
function showReconnect(err) {
  $("#reconnect-detail").textContent = errorMessage(err);
  showScreen("reconnect");
  $("#retry-connect").focus();
}

async function enterApp(user) {
  state.user = user;
  renderedDate = null; // 다른 사용자의 목록이 남지 않게
  state.date = today();
  state.weekStart = mondayOf(state.date);
  showScreen("app");
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

// 날짜·주를 빠르게 옮기면 응답이 요청 순서와 다르게 올 수 있다.
// 요청마다 번호를 붙이고, 가장 최근 요청의 응답만 화면에 그린다.
let logRequest = 0;
let weekRequest = 0;
let renderedDate = null;

async function renderLog() {
  const t = today();
  const date = state.date;
  const request = ++logRequest;
  $("#date-label").textContent = dateLabel(date);
  $("#next-day").disabled = date >= t;
  $("#go-today").hidden = date === t;
  const ul = $("#meal-list");
  if (renderedDate !== date) {
    // 다른 날짜의 목록이 새 제목 아래 남아 있지 않게 한다.
    renderedDate = null;
    ul.replaceChildren(el("li", { className: "loading", textContent: "불러오는 중…" }));
  }

  const [list, recent] = await Promise.all([
    guard(() => api(`/v1/meals?date=${date}`)),
    guard(() => api("/v1/meals/recent-descriptions")),
  ]);
  if (request !== logRequest || date !== state.date) return; // 늦게 온 이전 요청의 응답
  if (!list) return;
  renderedDate = date;

  ul.replaceChildren(...list.items.map(renderMeal));
  if (list.items.length === 0) {
    ul.append(el("li", { className: "empty", textContent: "아직 기록이 없어요. 생각나는 것 하나만 적어도 충분해요." }));
  }

  const box = $("#recent");
  box.replaceChildren(
    ...(recent?.items ?? []).map((text) => {
      const chip = el("button", { type: "button", className: "chip recent", title: text },
        el("span", { className: "chip-text", textContent: text }));
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
  }, "meal");
  button.disabled = false;
  if (!ok) return;
  toast(state.editingId ? "고쳤어요." : "기록했어요.");
  resetForm();
  await renderLog();
}

async function deleteMeal(meal) {
  if (!(await askConfirm(`"${meal.description}" 기록을 지울까요?`, "지우기"))) return;
  const ok = await guard(async () => {
    await api(`/v1/meals/${meal.id}`, { method: "DELETE" });
    return true;
  }, "meal");
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
  const request = ++weekRequest;
  const end = addDays(start, 6);
  $("#week-label").textContent = `${shortDate(start)} – ${shortDate(end)}`;
  $("#next-week").disabled = addDays(start, 7) > today();

  const s = await guard(() => api(`/v1/summaries/weekly?start=${start}`));
  if (request !== weekRequest || start !== state.weekStart) return; // 늦게 온 이전 요청의 응답
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
  let conflict = null;
  const user = await guard(async () => {
    try {
      return await api("/v1/auth/link", {
        method: "POST",
        body: { email: $("#link-email").value, password: $("#link-password").value },
      });
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) conflict = err.details[0]?.reason;
      throw err;
    }
  }, "link");
  if (conflict === "already_linked") {
    // 다른 탭이나 기기에서 이미 연결했다: 화면을 서버 상태에 맞춘다.
    const me = await guard(() => api("/v1/me"));
    if (me) { state.user = me; renderSettings(); }
  }
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
  if (state.user.email === null && !(await askConfirm(
    "계정을 연결하지 않으면 로그아웃 후 지금까지의 기록을 다시 볼 수 없어요. 그래도 로그아웃할까요?",
    "로그아웃",
  ))) {
    return;
  }
  await guard(() => api("/v1/auth/logout", { method: "POST" }));
  signOutLocally("로그아웃했어요.");
}

async function deleteAccount(event) {
  event.preventDefault();
  if (!(await askConfirm("계정과 모든 기록을 지금 삭제할까요? 되돌릴 수 없어요.", "삭제하고 탈퇴"))) return;
  const body = state.user.email === null ? undefined : { password: $("#delete-password").value };
  const ok = await guard(async () => {
    await api("/v1/me", { method: "DELETE", body });
    return true;
  }, "delete-account");
  if (!ok) return;
  $("#delete-form").reset();
  signOutLocally("탈퇴했어요. 모든 기록을 삭제했어요.");
}

// ---- 첫 화면 -------------------------------------------------------------------
// 다른 탭에서 시작했거나 하는 이유로 이미 토큰이 있으면, 덮어쓰기 전에 확인한다.
// 가입 없이 쓰던 사용자는 그 토큰이 기록으로 돌아갈 유일한 수단이다.
async function mayReplaceToken() {
  if (!tokenStore.get()) return true;
  return askConfirm(
    "이 브라우저에 이미 쓰고 있던 기록이 있어요. 계정을 연결하지 않았다면, 새로 시작하거나 다른 계정으로 로그인한 뒤에는 그 기록을 다시 볼 수 없어요. 계속할까요?",
    "계속하기",
  );
}

async function startAnonymous() {
  if (!(await mayReplaceToken())) return;
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
  if (!(await mayReplaceToken())) return;
  const data = await guard(() => api("/v1/auth/login", {
    method: "POST",
    body: { email: $("#login-email").value, password: $("#login-password").value },
  }), "login");
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
  $("#retry-connect").addEventListener("click", resume);
}

// 저장된 토큰으로 이어서 쓴다. 401(토큰이 무효)일 때만 토큰을 지우고 첫 화면으로 간다.
async function resume() {
  if (!tokenStore.get()) {
    showOnboarding();
    return;
  }
  const retry = $("#retry-connect");
  retry.disabled = true;
  let user;
  try {
    user = await api("/v1/me");
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) signOutLocally();
    else showReconnect(err);
    return;
  } finally {
    retry.disabled = false;
  }
  await enterApp(user);
}

async function boot() {
  $("#demo-banner").hidden = !config.demo;
  bind();
  await resume();
}

boot();
