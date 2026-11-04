/**
 * web/index.html(화면 원본)을 토스 미니앱용 index.html 로 변환.
 * - 완전한 HTML 문서로 감싸고
 * - 출시용 설정(window.SC_CONFIG)과 토스 SDK 연결부(src/bridge.js)를 넣음
 * 화면은 web/index.html 한 곳만 고치면 되고, 빌드할 때마다 자동으로 다시 만들어져요.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..");

function loadEnv(file) {
  if (!existsSync(file)) return {};
  return Object.fromEntries(
    readFileSync(file, "utf8")
      .split(/\r?\n/)
      .filter((l) => l.trim() && !l.trim().startsWith("#") && l.includes("="))
      .map((l) => {
        const i = l.indexOf("=");
        return [l.slice(0, i).trim(), l.slice(i + 1).trim().replace(/^["']|["']$/g, "")];
      }),
  );
}
const env = { ...loadEnv(join(root, ".env")), ...process.env };

const feedUrl = env.VITE_FEED_URL;
if (!feedUrl) {
  console.error("✗ VITE_FEED_URL 이 비어 있어요. toss-app/.env 에 공고 데이터 주소를 넣어주세요 (README 참고).");
  process.exit(1);
}

const cfg = {
  feedUrl,
  sample: env.SC_SAMPLE === "true", // 출시 빌드는 예시 공고 절대 안 보여줌
  onboarding: true,                 // 처음 연 사람은 "어떤 공고를 볼까요?" 부터
  defaultProfile: { status: "student", school: "other", sido: "서울", sigungu: "" },
};

const page = readFileSync(join(root, "..", "web", "index.html"), "utf8");
const cut = page.indexOf('<div class="wrap">');
if (cut < 0) throw new Error('web/index.html 에서 <div class="wrap"> 를 못 찾았어요');
const headPart = page.slice(0, cut).replace(/<meta name="claude:[^>]*>\s*/g, "");
const bodyPart = page.slice(cut);

const html = `<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>
  body{margin:0}
  [hidden]{display:none!important}
  img{max-width:100%}
  :root{padding-bottom:env(safe-area-inset-bottom,0px)}
</style>
<script>window.SC_CONFIG = ${JSON.stringify(cfg)};</script>
<script type="module" src="./src/bridge.js"></script>
${headPart.trim()}
</head>
<body>
${bodyPart.trim()}
</body>
</html>
`;
writeFileSync(join(root, "index.html"), html);
console.log(`✓ index.html 생성 (공고 주소: ${feedUrl}${cfg.sample ? ", 예시 공고 켜짐" : ""})`);
