/** @type {import('next').NextConfig} */

// Content Security Policy configuration
// SECURITY: In production, remove 'unsafe-inline' and 'unsafe-eval' and use nonces instead
const isDev = process.env.NODE_ENV === 'development'

const cspDirectives = {
  'default-src': ["'self'"],
  'script-src': [
    "'self'",
    "'unsafe-inline'", // Required for Next.js hydration scripts
    ...(isDev ? ["'unsafe-eval'"] : []), // unsafe-eval only in development
    "https://va.vercel-scripts.com", // Vercel Analytics
    "https://vercel.live", // Vercel Live
    "https://apis.google.com", // Google Sign-In
    "https://www.gstatic.com", // Google scripts
    "https://accounts.google.com", // Google accounts
    "https://www.googletagmanager.com", // Google Tag Manager / Analytics
  ],
  'style-src': ["'self'", "'unsafe-inline'"], // inline styles for Tailwind (required)
  // SECURITY: Restrict img-src to specific trusted domains instead of all https
  'img-src': [
    "'self'",
    "data:",
    "blob:",
    "https://lh3.googleusercontent.com", // Google profile photos
    "https://firebasestorage.googleapis.com", // Firebase storage
    "https://www.gstatic.com", // Google static assets
    "https://*.fal.media", // fal.ai generated images
    "https://www.googletagmanager.com", // Google Analytics tracking pixels
  ],
  'font-src': ["'self'", "data:"],
  'connect-src': [
    "'self'",
    "http://localhost:*", // Local API for dev
    "http://192.168.1.100:*", // LAN IP for dev
    "http://122.166.148.116:*", // External IP for dev
    "https://api.d23ai.in", // Production API
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
    "https://www.google-analytics.com", // Google Analytics
    "https://*.google-analytics.com", // Google Analytics
    "https://*.analytics.google.com", // Google Analytics
    "ws://localhost:*", // WebSocket for dev
    "wss://localhost:*",
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

  images: {
    // Enable image optimization for production
    unoptimized: process.env.NODE_ENV === 'development',
    // SECURITY: Restrict remote patterns to trusted domains only
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'lh3.googleusercontent.com', // Google profile photos
      },
      {
        protocol: 'https',
        hostname: 'firebasestorage.googleapis.com', // Firebase storage
      },
      {
        protocol: 'https',
        hostname: '*.googleapis.com', // Google APIs
      },
      {
        protocol: 'https',
        hostname: 'www.gstatic.com', // Google static assets
      },
      {
        protocol: 'https',
        hostname: '*.fal.media', // fal.ai generated images
      },
    ],
  },

  // Proxy API requests to backend
  // Uses API_URL env variable, or defaults based on environment
  async rewrites() {
    // Allow override via environment variable
    const apiUrl = process.env.API_URL
      || (process.env.NODE_ENV === 'production'
        ? 'http://localhost:9002'  // OhGrtApi backend
        : 'http://localhost:9002')

    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/:path*`,
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
