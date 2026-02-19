/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Enable SWC minification for faster builds
  swcMinify: true,

  // Environment variables validation
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
  },

  // API route rewrites to backend (optional, for proxying)
  async rewrites() {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    
    return [
      {
        source: '/api/backend/:path*',
        destination: `${apiBaseUrl}/:path*`,
      },
    ];
  },

  // Headers for security
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ];
  },

  // Webpack configuration (if needed for custom loaders)
  webpack: (config, { isServer }) => {
    // Custom webpack configuration here if needed
    return config;
  },

  // Experimental features (enable as needed)
  experimental: {
    // Enable if using server actions
    // serverActions: true,
  },

  // Image optimization
  images: {
    domains: [
      'avatars.githubusercontent.com', // GitHub user avatars
      'github.com', // GitHub resources
    ],
  },

  // Output configuration (standalone for Docker)
  output: 'standalone',

  // TypeScript configuration
  typescript: {
    // Set to true to allow production builds to successfully complete
    // even if your project has type errors
    ignoreBuildErrors: false,
  },

  // ESLint configuration
  eslint: {
    // Only run ESLint on these directories during production builds
    dirs: ['src'],
  },
};

module.exports = nextConfig;
