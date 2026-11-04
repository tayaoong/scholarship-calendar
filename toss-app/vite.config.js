import { defineConfig } from "vite";

export default defineConfig({
  base: "./", // 미니앱 번들 안에서 상대 경로로 읽히게
  build: { outDir: "dist", emptyOutDir: true },
});
