import { defineConfig } from "@apps-in-toss/web-framework/config";

export default defineConfig({
  // ⚠️ 앱인토스 콘솔에 등록한 앱 이름(영문 kebab-case)과 똑같아야 업로드돼요.
  appName: "naedon-naechat",
  brand: {
    primaryColor: "#3182F6",
  },
  permissions: [],
  navigationBar: {
    withBackButton: true,
    withHomeButton: true,
    withTitle: true,
  },
  webView: {
    bounces: false,
    pullToRefreshEnabled: false,
  },
  webBundleDir: "dist",
});
