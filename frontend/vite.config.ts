import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const backendUrl = env.VITE_API_BASE_URL;

  return {
    plugins: [react()],
    server: {
      host: "127.0.0.1",
      port: 5173,
      proxy: backendUrl
        ? {
            "/__api": {
              target: backendUrl,
              changeOrigin: true,
              rewrite: (path) => path.replace(/^\/__api/, "")
            }
          }
        : undefined
    }
  };
});
