/**
 * Environment variable validation
 *
 * SECURITY: Validates that all required environment variables are set
 * This prevents the app from running with missing configuration
 */

// Required environment variables for the app to function
const requiredEnvVars = [
  'NEXT_PUBLIC_API_URL',
  'NEXT_PUBLIC_FIREBASE_API_KEY',
  'NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN',
  'NEXT_PUBLIC_FIREBASE_PROJECT_ID',
] as const;

// Optional but recommended environment variables
const recommendedEnvVars = [
  'NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET',
  'NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID',
  'NEXT_PUBLIC_FIREBASE_APP_ID',
] as const;

interface EnvValidationResult {
  isValid: boolean;
  missing: string[];
  warnings: string[];
}

/**
 * Validate that all required environment variables are set
 * Call this at app startup to catch configuration errors early
 */
export function validateEnv(): EnvValidationResult {
  const missing: string[] = [];
  const warnings: string[] = [];

  // Check required variables
  for (const key of requiredEnvVars) {
    if (!process.env[key]) {
      missing.push(key);
    }
  }

  // Check recommended variables
  for (const key of recommendedEnvVars) {
    if (!process.env[key]) {
      warnings.push(key);
    }
  }

  const isValid = missing.length === 0;

  if (!isValid) {
    console.error(`[ENV] Missing required environment variables: ${missing.join(', ')}`);
  }

  if (warnings.length > 0) {
    console.warn(`[ENV] Missing recommended environment variables: ${warnings.join(', ')}`);
  }

  return { isValid, missing, warnings };
}

/**
 * Get a required environment variable, throwing if not set
 */
export function getRequiredEnv(key: string): string {
  const value = process.env[key];
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value;
}

/**
 * Get an optional environment variable with a fallback
 */
export function getOptionalEnv(key: string, fallback: string): string {
  return process.env[key] || fallback;
}

/**
 * Check if we're in production mode
 */
export function isProduction(): boolean {
  return process.env.NODE_ENV === 'production';
}

/**
 * Check if we're in development mode
 */
export function isDevelopment(): boolean {
  return process.env.NODE_ENV === 'development';
}

// Validate on module load in development
if (typeof window === 'undefined' && process.env.NODE_ENV !== 'test') {
  const result = validateEnv();
  if (!result.isValid && process.env.NODE_ENV === 'production') {
    throw new Error(
      `Application cannot start: Missing required environment variables: ${result.missing.join(', ')}`
    );
  }
}
