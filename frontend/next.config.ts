import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export so FastAPI can serve the site from a plain directory.
  output: "export",
};

export default nextConfig;
