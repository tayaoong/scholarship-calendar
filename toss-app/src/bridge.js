/**
 * 토스 미니앱 연결부.
 * 화면(web/index.html)은 window.SCBridge 가 있으면 이걸 쓰고, 없으면 브라우저 기본 동작을 써요.
 * 그래서 같은 화면 파일이 일반 브라우저와 토스 앱 양쪽에서 돌아가요.
 */
import { Share, Device, TossAds, getOperationalEnvironment } from "@apps-in-toss/web-framework";

const APP_NAME = import.meta.env.VITE_APP_NAME || "naedon-naechat";
// 개발 중에는 반드시 테스트 ID. 실제 ID로 테스트하면 정책 위반이 될 수 있어요.
const AD_GROUP_ID = import.meta.env.VITE_AD_GROUP_ID || "ait-ad-test-banner-id";

function inToss() {
  try {
    const env = getOperationalEnvironment();
    return env === "toss" || env === "sandbox";
  } catch {
    return false; // 일반 브라우저
  }
}

/** 공유 메시지 끝에 미니앱 링크를 붙여서 친구가 바로 열 수 있게 */
async function share(message) {
  let link = "";
  try {
    link = await Share.createLink({ path: `intoss://${APP_NAME}` });
  } catch {
    /* 링크 생성 실패해도 메시지는 보냄 */
  }
  await Share.sendMessage({ message: link ? `${message}\n\n${link}` : message });
}

function attachBannerAd() {
  const slot = document.getElementById("adSlot");
  if (!slot) return;
  if (TossAds.initialize.isSupported && !TossAds.initialize.isSupported()) return;
  TossAds.initialize({
    callbacks: {
      onInitialized: () => {
        slot.hidden = false;
        TossAds.attachBanner(AD_GROUP_ID, slot, {
          theme: "auto",
          tone: "blackAndWhite",
          variant: "expanded",
          callbacks: {
            onNoFill: () => { slot.hidden = true; },
            onAdFailedToRender: () => { slot.hidden = true; },
          },
        });
      },
      onInitializationFailed: () => { slot.hidden = true; },
    },
  });
}

if (inToss()) {
  window.SCBridge = {
    share,
    openURL: (url) => Device.openURL(url),
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", attachBannerAd);
  else attachBannerAd();
}
