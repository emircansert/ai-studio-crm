/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Standalone output produces a minimal self-contained server bundle used by
  // the production Docker image.
  output: "standalone"
};

export default nextConfig;
