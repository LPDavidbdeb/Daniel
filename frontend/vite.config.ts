import react from "@vitejs/plugin-react"
import { defineConfig, loadEnv } from "vite"
import tailwindcss from "@tailwindcss/vite"

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "")
  const apiTarget = env.VITE_API_TARGET || "http://localhost:8080"

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": "/src",
      },
    },
    server: {
      port: 5173,
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: "./src/test/setup.ts",
    },
  }
})
