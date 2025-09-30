/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: 'standalone',
  experimental: {
    outputFileTracingRoot: undefined,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://backend:5000/api/:path*',
      },
      {
        source: '/auth/:path*',
        destination: 'http://backend:5000/auth/:path*',
      },
      {
        source: '/oauth/:path*',
        destination: 'http://backend:5000/oauth/:path*',
      },
      {
        source: '/token/:path*',
        destination: 'http://backend:5000/token/:path*',
      },
      {
        source: '/graphql',
        destination: 'http://backend:5000/graphql',
      },
    ];
  },
}

module.exports = nextConfig