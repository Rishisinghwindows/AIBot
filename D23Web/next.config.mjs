/** @type {import('next').NextConfig} */

// Content Security Policy configuration
const cspDirectives = {
  'default-src': ["'self'"],
  'script-src': [
    "'self'",
    "'unsafe-inline'",
    "'unsafe-eval'", // needed for Next.js dev
    "https://va.vercel-scripts.com", // Vercel Analytics
    "https://vercel.live", // Vercel Live
    "https://apis.google.com", // Google Sign-In
    "https://www.gstatic.com", // Google scripts
    "https://accounts.google.com", // Google accounts
  ],
  'style-src': ["'self'", "'unsafe-inline'"], // inline styles for Tailwind
  'img-src': ["'self'", "data:", "blob:", "https:"],
  'font-src': ["'self'", "data:"],
  'connect-src': [
    "'self'",
    "http://localhost:*", // Local API for dev
    "http://127.0.0.1:*", // Local API for dev (IP)
    "https://api.whatsapp.com",
    "https://accounts.google.com",
    "https://oauth2.googleapis.com",
    "https://*.googleapis.com", // Google APIs
    "https://*.firebaseio.com", // Firebase
    "https://*.firebase.google.com", // Firebase Auth
    "https://identitytoolkit.googleapis.com", // Firebase Auth API
    "https://securetoken.googleapis.com", // Firebase tokens
    "https://vitals.vercel-insights.com", // Vercel Analytics
    "https://va.vercel-scripts.com", // Vercel Analytics
    "ws://localhost:*", // WebSocket for dev
    "wss://localhost:*",
    "ws://d23ai.in",  // WebSocket for dev via domain (HTTP)
    "wss://d23ai.in", // WebSocket for dev via domain (HTTPS)
  ],
  'frame-src': [
    "'self'",
    "https://accounts.google.com",
    "https://*.firebaseapp.com", // Firebase Auth popup
  ],
  'frame-ancestors': ["'self'"],
  'form-action': ["'self'"],
  'base-uri': ["'self'"],
  'object-src': ["'none'"],
  'upgrade-insecure-requests': [],
}

const cspHeader = Object.entries(cspDirectives)
  .map(([key, values]) => `${key} ${values.join(' ')}`)
  .join('; ')

const nextConfig = {
  // TypeScript errors will now fail the build (recommended for production)
  // If you need to temporarily ignore errors during development, set:
  // typescript: { ignoreBuildErrors: true },

  // Allow dev server access from custom domain
  allowedDevOrigins: ['d23ai.in'],

  images: {
    // Enable image optimization for production
    unoptimized: process.env.NODE_ENV === 'development',
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },

  // Proxy API requests to backend (allows external access without exposing backend port)
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ]
  },

  // Security headers including CSP
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Content-Security-Policy',
            value: cspHeader,
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=(self), interest-cohort=()',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains',
          },
        ],
      },
    ]
  },
}

export default nextConfig
