import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the API runs on :8010; requests to /api are proxied to it.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5180,
    proxy: { "/api": process.env.VITE_API_TARGET ?? "http://localhost:8010" },
  },
});
