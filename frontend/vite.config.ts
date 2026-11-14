import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the API runs on :8010; requests to /api are proxied to it.
export default defineConfig({
  plugins: [react()],
  // Old browsers too (the family's old Mac): newer syntax is rewritten at build time
  build: { target: ["es2018", "safari12", "chrome70", "firefox68"] },
  server: {
    host: true,
    port: 5180,
    proxy: { "/api": process.env.VITE_API_TARGET ?? "http://localhost:8010" },
  },
});
