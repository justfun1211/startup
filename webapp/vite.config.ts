import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 3000,
    allowedHosts: [".ngrok-free.dev", ".ngrok.app", ".trycloudflare.com", "localhost"],
  },
});
