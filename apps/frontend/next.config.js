/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        // Browser calls /api/... → Next.js server proxies to backend container
        // This avoids CORS and localhost confusion entirely
        source: "/api/:path*",
        destination: `${process.env.BACKEND_URL || "http://backend:8000"}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
