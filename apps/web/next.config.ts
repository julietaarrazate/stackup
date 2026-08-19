import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // The API base URL is provided per-environment; never hardcode production
  // URLs (see ADR-007 / .env.example). The BFF layer (Route Handlers) reads
  // this server-side to reach FastAPI.
  env: {
    NEXT_PUBLIC_APP_NAME: "STACKUP",
  },
};

export default nextConfig;
