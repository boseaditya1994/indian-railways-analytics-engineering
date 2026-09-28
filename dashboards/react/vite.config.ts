import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ command }) => ({
  base: command === "build" ? "/indian-railways-analytics-engineering/" : "/",
  plugins: [react()],
  server: {
    proxy: {
      "/v1": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000"
    }
  }
}));
