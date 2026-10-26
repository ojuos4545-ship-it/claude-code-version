// 실제 백엔드와 웹을 띄우고 브라우저로 사용자 흐름(US-1~US-8)을 끝까지 수행한다.
// 실행: node web/tests/e2e.mjs   (저장소 루트에서, backend/.venv 준비 후)
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

// 전역 설치된 playwright도 찾도록 require로 불러온다(ESM import는 NODE_PATH를 보지 않음).
const { chromium } = createRequire(import.meta.url)("playwright");

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const API = "http://localhost:8000";
const WEB = "http://localhost:5173";
const dataDir = mkdtempSync(join(tmpdir(), "eml-e2e-"));

function start(cmd, args, opts) {
  const p = spawn(cmd, args, { stdio: ["ignore", "ignore", "pipe"], ...opts });
  let err = "";
  p.stderr.on("data", (d) => { err += d; });
  p.on("exit", (code) => { if (code) console.error(`${cmd} exited ${code}\n${err}`); });
  return p;
}

async function waitFor(url) {
  for (let i = 0; i < 100; i++) {
    try { if ((await fetch(url)).status < 500) return; } catch { /* 아직 안 뜸 */ }
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error(`${url} did not start`);
}

const backend = start(join(root, "backend/.venv/bin/uvicorn"), ["app.main:create_app", "--factory", "--port", "8000"], {
  cwd: join(root, "backend"),
  env: { ...process.env, APP_ENV: "development", APP_DATABASE_PATH: join(dataDir, "e2e.db") },
});
const web = start("python3", ["-m", "http.server", "5173", "--directory", join(root, "web")], {});

const steps = [];
const step = (name) => steps.push(name) && console.log(`- ${name}`);
let browser;
try {
  await waitFor(`${API}/v1/me`);
  await waitFor(WEB);
  browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 390, height: 844 }, timezoneId: "Asia/Seoul" });
  const consoleErrors = [];
  page.on("console", (m) => {
    // 의도된 401/403 응답은 브라우저가 콘솔에 남기므로 제외한다.
    if (m.type() === "error" && !/status of 40[13]/.test(m.text())) consoleErrors.push(m.text());
  });
  page.on("pageerror", (e) => consoleErrors.push(String(e)));
  // 확인은 화면 안 확인 창(#confirm-dialog)으로 받는다.
  const confirmOk = () => page.locator("#confirm-ok").click();
  const toast = () => page.locator("#toast").textContent();

  step("CSP: connect-src가 config.js의 API 주소와 같고, 인라인 스크립트는 막힌다");
  const html = readFileSync(join(root, "web/index.html"), "utf8");
  const csp = html.match(/http-equiv="Content-Security-Policy" content="([^"]+)"/)?.[1];
  assert.ok(csp, "index.html에 CSP meta 태그");
  const apiBase = readFileSync(join(root, "web/config.js"), "utf8").match(/apiBase:\s*"([^"]+)"/)[1];
  const connectSrc = csp.split(";").map((d) => d.trim()).find((d) => d.startsWith("connect-src "));
  assert.deepEqual(connectSrc.split(/\s+/).slice(1), [new URL(apiBase).origin], "connect-src == config.js apiBase");
  // 별도 페이지에서 확인한다(의도한 CSP 위반 메시지가 본 흐름의 콘솔 검사에 섞이지 않게).
  const probe = await browser.newPage();
  const violations = [];
  probe.on("console", (m) => { if (/Content Security Policy/.test(m.text())) violations.push(m.text()); });
  await probe.goto(WEB);
  const injected = await probe.evaluate(() => {
    const s = document.createElement("script");
    s.textContent = "window.__cspProbe = 1";
    document.head.append(s);
    return window.__cspProbe;
  });
  assert.equal(injected, undefined, "인라인 스크립트가 실행되면 안 됨");
  await probe.waitForTimeout(100);
  assert.ok(violations.length > 0, "CSP 위반이 보고됨");
  await probe.close();

  await page.goto(WEB);
  step("첫 화면: 동의 전에는 시작할 수 없다");
  assert.equal(await page.locator("#start-anonymous").isDisabled(), true);
  await page.getByLabel("[필수] 식단 기록의 수집·이용에 동의합니다").check();
  await page.getByRole("button", { name: "바로 시작하기" }).click();
  await page.locator("#app").waitFor();
  assert.match(await page.locator("#date-label").textContent(), /^오늘/);
  assert.equal(await page.locator("#next-day").isDisabled(), true, "미래로 갈 수 없다");

  step("US-1/2: 한 줄 + 양만 골라 기록");
  await page.getByLabel("무엇을 먹었나요?").fill("김치찌개");
  await page.getByRole("button", { name: "보통" }).click();
  await page.getByRole("button", { name: "기록하기" }).click();
  await page.locator(".meal").first().waitFor();
  assert.equal(await page.locator(".meal-desc").first().textContent(), "김치찌개");
  assert.equal(await page.locator(".meal-meta").first().textContent(), "보통");

  step("US-6: 최근 메뉴를 눌러 다시 기록");
  await page.locator("#recent .chip", { hasText: "김치찌개" }).click();
  assert.equal(await page.getByLabel("무엇을 먹었나요?").inputValue(), "김치찌개");
  await page.getByRole("button", { name: "기록하기" }).click();
  await page.waitForFunction(() => document.querySelectorAll(".meal").length === 2);

  step("빈 입력은 서버로 보내지 않고 안내만 한다");
  await page.getByRole("button", { name: "기록하기" }).click();
  assert.match(await toast(), /한 줄만/);

  step("US-3: 어제로 가서 몰아서 기록");
  await page.getByRole("button", { name: "전날" }).click();
  assert.match(await page.locator("#date-label").textContent(), /^어제/);
  assert.match(await page.locator(".empty").textContent(), /충분해요/);
  await page.getByLabel("무엇을 먹었나요?").fill("샐러드");
  await page.getByRole("button", { name: "점심" }).click();
  await page.getByRole("button", { name: "기록하기" }).click();
  await page.locator(".meal-desc", { hasText: "샐러드" }).waitFor();

  step("US-4: 고치고 지우기");
  await page.getByRole("button", { name: "샐러드 수정" }).click();
  await page.getByLabel("기록 고치기").fill("닭가슴살 샐러드");
  await page.getByRole("button", { name: "저장하기" }).click();
  await page.locator(".meal-desc", { hasText: "닭가슴살 샐러드" }).waitFor();
  await page.getByRole("button", { name: "오늘로" }).click();
  await page.getByRole("button", { name: "김치찌개 삭제" }).first().click();
  await confirmOk();
  await page.waitForFunction(() => document.querySelectorAll(".meal").length === 1);

  step("US-5/7: 한 주 보기는 기록한 날 수만 보여 준다");
  await page.getByRole("button", { name: "한 주" }).click();
  await page.locator("#week-headline", { hasText: "일 기록했어요" }).waitFor();
  const headline = await page.locator("#week-headline").textContent();
  // 이번 주 월요일이면 어제 기록은 지난주에 속한다.
  assert.match(headline, /이 주에 [12]일 기록했어요/);
  assert.doesNotMatch(await page.locator("#tab-week").textContent(), /실패|미달|점수|kcal|칼로리/);

  step("US-8: 이메일 연결 → 로그아웃 → 다시 로그인하면 기록이 그대로");
  await page.getByRole("button", { name: "설정" }).click();
  await page.locator("#link-email").fill("e2e@example.com");
  await page.locator("#link-password").fill("e2e-password");
  await page.getByRole("button", { name: "연결하기" }).click();
  await page.locator("#account-email", { hasText: "e2e@example.com" }).waitFor();
  await page.getByRole("button", { name: "로그아웃" }).click();
  await page.locator("#onboarding").waitFor();
  await page.getByText("이미 이메일 계정이 있어요").click();
  await page.locator("#onboarding").getByLabel("이메일").fill("e2e@example.com");
  await page.locator("#onboarding").getByLabel("비밀번호").fill("wrong-password");
  await page.getByRole("button", { name: "로그인" }).click();
  await page.locator("#toast", { hasText: "맞지 않아요" }).waitFor();
  await page.locator("#onboarding").getByLabel("비밀번호").fill("e2e-password");
  await page.getByRole("button", { name: "로그인" }).click();
  await page.locator(".meal-desc", { hasText: "김치찌개" }).waitFor();

  step("레이아웃: 휴대폰 폭에서 가로 스크롤이 없다");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  assert.equal(overflow, false);

  step("US-8: 비밀번호를 확인하고 탈퇴하면 처음 화면으로");
  await page.getByRole("button", { name: "설정" }).click();
  await page.getByLabel("비밀번호 확인").fill("e2e-password");
  await page.getByRole("button", { name: "모든 기록 삭제하고 탈퇴" }).click();
  await confirmOk();
  await page.locator("#onboarding").waitFor();
  const r = await fetch(`${API}/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: "e2e@example.com", password: "e2e-password" }),
  });
  assert.equal(r.status, 401, "탈퇴 후 로그인 불가");

  step("가입 없이 시작한 사용자는 비밀번호 없이 탈퇴할 수 있다");
  await page.getByLabel("[필수] 식단 기록의 수집·이용에 동의합니다").check();
  await page.getByRole("button", { name: "바로 시작하기" }).click();
  await page.getByRole("button", { name: "설정" }).click();
  assert.equal(await page.locator("#delete-password-row").isHidden(), true);
  await page.getByRole("button", { name: "모든 기록 삭제하고 탈퇴" }).click();
  await confirmOk();
  await page.locator("#onboarding").waitFor();

  assert.deepEqual(consoleErrors, [], "브라우저 콘솔 오류 없음");
  console.log(`\nPASS: ${steps.length}개 단계`);
} catch (err) {
  console.error(`\nFAIL at: ${steps.at(-1)}\n`, err);
  process.exitCode = 1;
} finally {
  await browser?.close();
  backend.kill();
  web.kill();
  rmSync(dataDir, { recursive: true, force: true });
}
