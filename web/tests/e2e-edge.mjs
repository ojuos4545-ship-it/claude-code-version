// e2e.mjs가 다루지 않는 경계·실패 상황. 실제 백엔드와 정적 서버를 띄워 브라우저로 확인한다.
// 실행: node web/tests/e2e-edge.mjs   (저장소 루트에서, backend/.venv 준비 후, 8000·5173 포트가 비어 있어야 함)
// 한 단계가 실패해도 나머지를 계속 돌리고, 끝에 실패 목록을 출력한다.
// "[버그 재현]" 단계는 2026-10-26 출시 전 QA에서 찾은 버그를 재현하며, 제품 코드가 고쳐지기 전까지 실패한다.
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const { chromium } = createRequire(import.meta.url)("playwright");

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const API = "http://localhost:8000";
const WEB = "http://localhost:5173";
const dataDir = mkdtempSync(join(tmpdir(), "eml-e2e-edge-"));
const DB = join(dataDir, "edge.db");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function spawnProc(cmd, args, opts) {
  return spawn(cmd, args, { stdio: "ignore", ...opts });
}
async function waitFor(url) {
  for (let i = 0; i < 150; i++) {
    try { if ((await fetch(url)).status < 500) return; } catch { /* 아직 안 뜸 */ }
    await sleep(100);
  }
  throw new Error(`${url} did not start`);
}
async function stop(p) {
  if (!p || p.exitCode !== null) return;
  const done = new Promise((r) => p.on("exit", r));
  p.kill();
  await done;
}
async function startBackend() {
  const p = spawnProc(join(root, "backend/.venv/bin/uvicorn"), ["app.main:create_app", "--factory", "--port", "8000"], {
    cwd: join(root, "backend"),
    // 같은 IP로 '바로 시작'을 여러 번 하므로 요청 수 제한은 끈다(제한 문구는 모의 응답으로 확인).
    env: { ...process.env, APP_ENV: "development", APP_DATABASE_PATH: DB, APP_RATE_LIMIT_ENABLED: "false" },
  });
  await waitFor(`${API}/healthz`);
  return p;
}
const isoIn = (timeZone) => new Intl.DateTimeFormat("en-CA", { timeZone }).format(new Date());

let backend = await startBackend();
const web = spawnProc("python3", ["-m", "http.server", "5173", "--directory", join(root, "web")], {});
await waitFor(WEB);
const browser = await chromium.launch();

const failures = [];
let count = 0;
async function step(name, fn) {
  count++;
  try {
    await fn();
    console.log(`ok   ${name}`);
  } catch (err) {
    failures.push(name);
    console.log(`FAIL ${name}\n     ${String(err?.message ?? err).split("\n")[0]}`);
  }
}

async function open({ timezoneId = "Asia/Seoul", viewport = { width: 390, height: 844 } } = {}) {
  const ctx = await browser.newContext({ timezoneId, viewport });
  const page = await ctx.newPage();
  return { ctx, page };
}
async function startAnon(page) {
  await page.goto(WEB);
  await page.locator("#consent").check();
  await page.locator("#start-anonymous").click();
  await page.locator("#meal-list li").first().waitFor();
}
async function addMeal(page, text) {
  await page.locator("#description").fill(text);
  await page.locator("#save").click();
  await page.locator(".meal-desc", { hasText: text }).first().waitFor();
}
async function toast(page) {
  await page.locator("#toast").waitFor();
  return page.locator("#toast").textContent();
}
const errorBody = (status, code) => ({
  status,
  contentType: "application/json",
  headers: { "Access-Control-Allow-Origin": WEB },
  body: JSON.stringify({ error: { code, message: "x", details: [] } }),
});

try {
  await step("시간대: LA 브라우저로 시작하면 LA의 오늘로 기록된다", async () => {
    const { ctx, page } = await open({ timezoneId: "America/Los_Angeles" });
    await startAnon(page);
    await addMeal(page, "LA 기록");
    const token = await page.evaluate(() => localStorage.getItem("easy-meal-log.token"));
    const r = await (await fetch(`${API}/v1/meals?date=${isoIn("America/Los_Angeles")}`, { headers: { Authorization: `Bearer ${token}` } })).json();
    assert.equal(r.items.length, 1);
    await ctx.close();
  });

  await step("경계: 윤년 3월 1일의 전날은 2월 29일, 주 범위는 월~일", async () => {
    const { ctx, page } = await open();
    await page.clock.setFixedTime(new Date("2024-03-01T10:00:00+09:00"));
    await startAnon(page);
    await page.locator("#prev-day").click();
    await page.locator("#date-label", { hasText: "어제 · 2월 29일 (목)" }).waitFor();
    await addMeal(page, "윤일 기록");
    await page.locator('.tab[data-tab="week"]').click();
    await page.locator("#week-headline", { hasText: "이 주에 1일 기록했어요" }).waitFor();
    assert.equal(await page.locator("#week-label").textContent(), "2월 26일 – 3월 3일");
    assert.equal(await page.locator("#next-week").isDisabled(), true);
    await ctx.close();
  });

  await step("새로고침해도 로그인과 기록이 유지된다", async () => {
    const { ctx, page } = await open();
    await startAnon(page);
    await addMeal(page, "새로고침");
    await page.reload();
    await page.locator(".meal-desc", { hasText: "새로고침" }).waitFor();
    await ctx.close();
  });

  await step("느린 네트워크에서 저장 버튼 연타·Enter 연타해도 1건만 저장된다", async () => {
    const { ctx, page } = await open();
    await startAnon(page);
    await page.route("**/v1/meals", async (route) => {
      if (route.request().method() === "POST") await sleep(800);
      await route.continue();
    });
    await page.locator("#description").fill("연타");
    await page.locator("#save").dblclick();
    await page.locator(".meal-desc", { hasText: "연타" }).waitFor();
    await page.locator("#description").fill("엔터");
    for (let i = 0; i < 5; i++) await page.locator("#description").press("Enter");
    await sleep(1500);
    const items = await page.locator(".meal-desc").allTextContents();
    assert.deepEqual(items.sort(), ["엔터", "연타"]);
    await ctx.close();
  });

  await step("응답만 유실돼도 같은 Idempotency-Key 재시도로 1건만 생긴다", async () => {
    const { ctx, page } = await open();
    await startAnon(page);
    let n = 0;
    await page.route("**/v1/meals", async (route) => {
      if (route.request().method() !== "POST") return route.continue();
      if (++n === 1) { await route.fetch(); return route.abort("connectionreset"); }
      return route.continue();
    });
    await addMeal(page, "응답 유실");
    await sleep(300);
    assert.equal(n, 2);
    assert.equal((await page.locator(".meal-desc").allTextContents()).length, 1);
    await ctx.close();
  });

  await step("네트워크가 끊기면 안내하고 입력은 남겨 둔다", async () => {
    const { ctx, page } = await open();
    await startAnon(page);
    await ctx.setOffline(true);
    await page.locator("#description").fill("오프라인");
    await page.locator("#save").click();
    assert.match(await toast(page), /연결이 불안정해요/);
    assert.equal(await page.locator("#description").inputValue(), "오프라인");
    await ctx.close();
  });

  await step("429 응답은 '잠시 후 다시' 안내", async () => {
    const { ctx, page } = await open();
    await page.route("**/v1/auth/anonymous", (route) => route.fulfill(errorBody(429, "rate_limited")));
    await page.goto(WEB);
    await page.locator("#consent").check();
    await page.locator("#start-anonymous").click();
    assert.match(await toast(page), /시도가 많았어요/);
    await ctx.close();
  });

  await step("메모의 줄바꿈·이모지와 HTML 문자열은 글자 그대로 보인다", async () => {
    const { ctx, page } = await open();
    await startAnon(page);
    await page.locator("#description").fill('<img src=x onerror="window.__x=1">');
    await page.locator("#memo-box summary").click();
    await page.locator("#memo").fill("첫 줄\n둘째 줄 😀");
    await page.locator("#save").click();
    await page.locator(".meal-memo").waitFor();
    assert.equal(await page.locator(".meal-memo").innerText(), "첫 줄\n둘째 줄 😀");
    assert.equal(await page.locator("#meal-list img").count(), 0);
    assert.equal(await page.evaluate(() => window.__x), undefined);
    await ctx.close();
  });

  await step("[버그 재현] 403 https_required를 '비밀번호가 맞지 않아요'로 안내하지 않는다", async () => {
    const { ctx, page } = await open();
    await startAnon(page);
    await page.route("**/v1/meals", (route) => (route.request().method() === "POST"
      ? route.fulfill(errorBody(403, "https_required")) : route.continue()));
    await page.locator("#description").fill("보안 연결");
    await page.locator("#save").click();
    assert.doesNotMatch(await toast(page), /비밀번호/);
    await ctx.close();
  });

  await step("[버그 재현] 띄어쓰기 없는 긴 메뉴가 최근 메뉴에 있어도 휴대폰 폭에서 가로로 넘치지 않는다", async () => {
    const { ctx, page } = await open();
    await startAnon(page);
    await addMeal(page, "김치찌개에밥반공기랑계란말이두개그리고어묵볶음조금먹고후식으로사과반쪽");
    await page.locator("#recent .chip").first().waitFor();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    assert.ok(overflow <= 0, `가로 넘침 ${overflow}px`);
    await ctx.close();
  });

  await step("[버그 재현] 느린 응답 중 날짜를 빠르게 옮겨도 제목과 목록이 같은 날짜다", async () => {
    const { ctx, page } = await open();
    await startAnon(page);
    await addMeal(page, "오늘 기록");
    await page.locator("#prev-day").click();
    await page.locator(".empty").waitFor();
    await addMeal(page, "어제 기록");
    await page.route(`**/v1/meals?date=${isoIn("Asia/Seoul")}`, async (route) => { await sleep(1500); await route.continue(); });
    await page.locator("#next-day").click();
    await sleep(150);
    await page.locator("#prev-day").click();
    await sleep(2500);
    assert.match(await page.locator("#date-label").textContent(), /^어제/);
    assert.deepEqual(await page.locator(".meal-desc").allTextContents(), ["어제 기록"]);
    await ctx.close();
  });

  await step("[버그 재현] 서버가 잠시 안 될 때 앱을 열어도 가입 없이 쓰던 기록을 잃지 않는다", async () => {
    const { ctx, page } = await open();
    await startAnon(page);
    await addMeal(page, "잃으면 안 되는 기록");
    await stop(backend);
    await page.reload();
    await sleep(500);
    // 첫 화면(바로 시작하기)이 보이면, 사용자가 누르는 순간 기존 토큰이 새 익명 계정으로 덮어써진다.
    const startVisible = await page.locator("#start-anonymous").isVisible();
    backend = await startBackend();
    if (startVisible) {
      await page.locator("#consent").check();
      await page.locator("#start-anonymous").click();
      await page.locator("#meal-list li").first().waitFor();
    } else {
      await page.reload();
    }
    await page.locator(".meal-desc", { hasText: "잃으면 안 되는 기록" }).waitFor({ timeout: 3000 });
    await ctx.close();
  });

  // ---- 2026-10-26 수정 확인 단계 ------------------------------------------------
  await step("[1] 앱을 열 때 /v1/me가 503·429면 '다시 시도' 화면을 보이고 토큰을 지키며, 다시 시도로 이어서 쓴다", async () => {
    const { ctx, page } = await open();
    await startAnon(page);
    await addMeal(page, "다시 시도 기록");
    const token = await page.evaluate(() => localStorage.getItem("easy-meal-log.token"));
    for (const [status, code] of [[503, "server_busy"], [429, "rate_limited"]]) {
      await page.route("**/v1/me", (route) => route.fulfill(errorBody(status, code)));
      await page.reload();
      await page.locator("#reconnect").waitFor();
      assert.equal(await page.locator("#onboarding").isVisible(), false);
      assert.match(await page.locator("#reconnect-detail").textContent(), /잠시 후 다시/);
      assert.equal(await page.evaluate(() => localStorage.getItem("easy-meal-log.token")), token);
      await page.unroute("**/v1/me");
    }
    await page.locator("#retry-connect").click();
    await page.locator(".meal-desc", { hasText: "다시 시도 기록" }).waitFor();
    await ctx.close();
  });

  await step("[1] 첫 화면에서 이미 토큰이 있으면 '바로 시작하기'·로그인 전에 확인하고, 취소하면 토큰을 그대로 둔다", async () => {
    const ctx = await browser.newContext({ timezoneId: "Asia/Seoul", viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();
    // 화면 안 확인 창의 문구를 모으고 매번 취소한다.
    const dialogs = [];
    const dismiss = async () => {
      await page.locator("#confirm-dialog[open]").waitFor();
      dialogs.push(await page.locator("#confirm-message").textContent());
      await page.locator("#confirm-cancel").click();
    };
    await page.goto(WEB);
    // 다른 탭에서 시작한 경우처럼, 첫 화면이 떠 있는 동안 토큰이 생긴다.
    await page.evaluate(() => localStorage.setItem("easy-meal-log.token", "existing-token"));
    await page.locator("#consent").check();
    await page.locator("#start-anonymous").click();
    await dismiss();
    await page.locator("#login-box summary").click();
    await page.locator("#login-email").fill("x@example.com");
    await page.locator("#login-password").fill("password-123");
    await page.locator("#login-form button[type=submit]").click();
    await dismiss();
    assert.equal(dialogs.length, 2);
    assert.match(dialogs[0], /이미 쓰고 있던 기록/);
    assert.equal(await page.evaluate(() => localStorage.getItem("easy-meal-log.token")), "existing-token");
    assert.equal(await page.locator("#onboarding").isVisible(), true);
    await ctx.close();
  });

  await step("[4] 오류 문구: 503·탈퇴 비밀번호 403·제어 문자 422·긴 로그인 비밀번호·409 두 가지", async () => {
    const { ctx, page } = await open();
    await startAnon(page);
    // 503 server_busy
    await page.route("**/v1/meals", (route) => (route.request().method() === "POST"
      ? route.fulfill({ ...errorBody(503, "server_busy"), headers: { "Access-Control-Allow-Origin": WEB, "Retry-After": "1" } })
      : route.continue()));
    await page.locator("#description").fill("바쁨");
    await page.locator("#save").click();
    assert.match(await toast(page), /잠시 후 다시/);
    await page.unroute("**/v1/meals");
    // 탭이 든 설명(실제 서버 422): 길이 안내가 아니라 한 줄 안내
    await page.locator("#description").fill("밥\t국");
    await page.locator("#save").click();
    await page.locator("#toast", { hasText: "한 줄로" }).waitFor();
    assert.doesNotMatch(await page.locator("#toast").textContent(), /200자/);
    // 409: 이미 쓰는 이메일(실제 서버)
    await fetch(`${API}/v1/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "taken@example.com", password: "password-123", privacy_consent: true }),
    });
    await page.locator('.tab[data-tab="settings"]').click();
    await page.locator("#link-email").fill("taken@example.com");
    await page.locator("#link-password").fill("password-123");
    await page.locator("#link-form button[type=submit]").click();
    await page.locator("#toast", { hasText: "이미 다른 계정에서 쓰고 있는 이메일" }).waitFor();
    // 409: 다른 탭에서 이미 연결함(실제 서버) → 안내 후 화면을 서버 상태로 맞춘다
    const token = await page.evaluate(() => localStorage.getItem("easy-meal-log.token"));
    await fetch(`${API}/v1/auth/link`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ email: "other-tab@example.com", password: "password-123" }),
    });
    await page.locator("#link-email").fill("again@example.com");
    await page.locator("#link-password").fill("password-123");
    await page.locator("#link-form button[type=submit]").click();
    await page.locator("#toast", { hasText: "이미 이메일이 연결돼 있어요" }).waitFor();
    await page.locator("#account-email", { hasText: "other-tab@example.com" }).waitFor();
    // 탈퇴 비밀번호가 틀리면(실제 서버 403 forbidden) 비밀번호 안내
    await page.locator("#delete-password").fill("wrong-password");
    await page.locator("#delete-form button[type=submit]").click();
    await page.locator("#confirm-ok").click();
    await page.locator("#toast", { hasText: "비밀번호가 맞지 않아요" }).waitFor();
    await ctx.close();

    // 로그인 비밀번호 129자(실제 서버 422): "8자 이상"이 아니다
    const second = await open();
    await second.page.goto(WEB);
    await second.page.locator("#login-box summary").click();
    await second.page.locator("#login-email").fill("taken@example.com");
    await second.page.locator("#login-password").fill("p".repeat(129));
    await second.page.locator("#login-form button[type=submit]").click();
    const msg = await toast(second.page);
    assert.doesNotMatch(msg, /8자 이상/);
    assert.match(msg, /128자/);
    await second.ctx.close();
  });

  await step("[6] 긴 최근 메뉴 칩은 줄바꿈되고 두 줄까지만 보이며 320px에서도 가로로 넘치지 않는다", async () => {
    const { ctx, page } = await open({ viewport: { width: 320, height: 640 } });
    await startAnon(page);
    const long = "김치찌개에밥반공기랑계란말이두개그리고어묵볶음조금먹고후식으로사과반쪽".repeat(3);
    await addMeal(page, long);
    const chip = page.locator("#recent .chip").first();
    await chip.waitFor();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    assert.ok(overflow <= 0, `가로 넘침 ${overflow}px`);
    const lines = await chip.locator(".chip-text").evaluate((n) => Math.round(n.getBoundingClientRect().height / parseFloat(getComputedStyle(n).lineHeight)));
    assert.ok(lines <= 2, `칩 ${lines}줄`);
    assert.equal(await chip.getAttribute("title"), long);
    await chip.click();
    assert.equal(await page.locator("#description").inputValue(), long);
    await ctx.close();
  });

  await step("[7] 느린 응답 중 주를 빠르게 옮겨도 제목과 요약이 같은 주다", async () => {
    const { ctx, page } = await open();
    await startAnon(page);
    await addMeal(page, "이번 주 기록");
    await page.locator('.tab[data-tab="week"]').click();
    await page.locator("#week-headline", { hasText: "1일 기록했어요" }).waitFor();
    await page.locator("#prev-week").click();
    await page.locator("#week-headline", { hasText: "아직 기록이 없어요" }).waitFor();
    // 다음 주(=이번 주) 요약만 늦게 온다: 다음 주로 갔다가 바로 지난주로 돌아온다.
    const label = await page.locator("#week-label").textContent();
    let slowStart = null;
    await page.route("**/v1/summaries/weekly?start=*", async (route) => {
      const start = new URL(route.request().url()).searchParams.get("start");
      if (slowStart === null) slowStart = start;
      if (start === slowStart) await sleep(1500);
      await route.continue();
    });
    await page.locator("#next-week").click();
    await sleep(150);
    await page.locator("#prev-week").click();
    await sleep(2500);
    assert.equal(await page.locator("#week-label").textContent(), label);
    assert.match(await page.locator("#week-headline").textContent(), /아직 기록이 없어요/);
    await ctx.close();
  });
} finally {
  await browser.close();
  await stop(backend);
  await stop(web);
  rmSync(dataDir, { recursive: true, force: true });
  console.log(`\n${count}개 단계 중 실패 ${failures.length}개${failures.length ? `:\n- ${failures.join("\n- ")}` : ""}`);
  if (failures.length) process.exitCode = 1;
}
