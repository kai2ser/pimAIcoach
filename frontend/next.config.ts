import type { NextConfig } from "next";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  // Enable modern image formats for smaller file sizes
  images: {
    formats: ["image/avif", "image/webp"],
  },

  // Enable gzip compression
  compress: true,

  async rewrites() {
    return [
      {
        source: "/api/coach/:path*",
        destination: `${BACKEND_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
