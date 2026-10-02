import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The e2e suite runs its own server in a separate build directory, so `make test`
  // works while `make web-dev` is running (one dev server per directory).
  distDir: process.env.NEXT_DIST_DIR ?? ".next",
};

export default nextConfig;
