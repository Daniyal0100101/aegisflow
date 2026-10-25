/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    // Disable during production build to avoid compilation stalls during containerization
    ignoreDuringBuilds: true,
  }
};

export default nextConfig;
