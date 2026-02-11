import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Use rewrites to proxy API requests to the backend
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.API_URL || "http://localhost:8080"}/api/:path*`,
      },
      // Also proxy auth endpoints if they are at root
      {
        source: "/auth/:path*",
        destination: `${process.env.API_URL || "http://localhost:8080"}/auth/:path*`,
      },
    ];
  },
};

export default nextConfig;
