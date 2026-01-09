/**
 * Authenticated fetch wrapper with automatic token refresh
 *
 * This module handles:
 * 1. Adding Authorization header to requests
 * 2. Automatically refreshing access token on 401 errors
 * 3. Redirecting to login when refresh fails
 */

// Use Next.js proxy to avoid CORS issues
const API_URL = '/api';

// Track if we're currently refreshing to prevent multiple refresh attempts
let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

/**
 * Refresh the access token using the refresh token
 */
async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = typeof window !== 'undefined'
    ? localStorage.getItem("refresh_token")
    : null;

  if (!refreshToken) {
    console.log("[AuthFetch] No refresh token available");
    return null;
  }

  try {
    console.log("[AuthFetch] Refreshing access token...");
    const response = await fetch(`${API_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      console.error("[AuthFetch] Token refresh failed:", response.status);
      return null;
    }

    const data = await response.json();
    console.log("[AuthFetch] Token refresh successful");

    // Update localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem("access_token", data.access_token);
      if (data.refresh_token) {
        localStorage.setItem("refresh_token", data.refresh_token);
      }
    }

    return data.access_token;
  } catch (error) {
    console.error("[AuthFetch] Error refreshing token:", error);
    return null;
  }
}

/**
 * Handle session expiration - clear tokens and redirect to login
 */
function handleSessionExpired(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("firebase_id_token");

    // Redirect to login page
    window.location.href = '/login';
  }
}

/**
 * Get a valid access token, refreshing if necessary
 */
async function getValidToken(): Promise<string | null> {
  const accessToken = typeof window !== 'undefined'
    ? localStorage.getItem("access_token")
    : null;

  return accessToken;
}

/**
 * Authenticated fetch with automatic token refresh on 401
 *
 * @param url - The URL to fetch
 * @param options - Fetch options
 * @param token - Optional token override (if not provided, uses localStorage)
 * @returns Response from the fetch
 */
const authFetch = async (
  url: string,
  options: RequestInit = {},
  token?: string | null
): Promise<Response> => {
  // Get the auth token
  const authToken = token ?? (typeof window !== 'undefined'
    ? (localStorage.getItem("access_token") || localStorage.getItem("firebase_id_token"))
    : null);

  // Set up headers with auth
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> || {}),
  };

  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }

  // Make the initial request
  const response = await fetch(url, {
    ...options,
    headers,
  });

  // If not 401, return the response as-is
  if (response.status !== 401) {
    return response;
  }

  // Handle 401 - attempt token refresh
  console.log("[AuthFetch] Got 401, attempting token refresh...");

  // Prevent multiple simultaneous refresh attempts
  if (!isRefreshing) {
    isRefreshing = true;
    refreshPromise = refreshAccessToken();
  }

  try {
    const newToken = await refreshPromise;

    if (!newToken) {
      // Refresh failed - redirect to login
      console.log("[AuthFetch] Token refresh failed, redirecting to login");
      handleSessionExpired();
      return response; // Return original 401 response
    }

    // Retry the original request with new token
    console.log("[AuthFetch] Retrying request with new token");
    const retryResponse = await fetch(url, {
      ...options,
      headers: {
        ...headers,
        Authorization: `Bearer ${newToken}`,
      },
    });

    return retryResponse;
  } finally {
    isRefreshing = false;
    refreshPromise = null;
  }
};

/**
 * Check if user is authenticated (has valid tokens)
 */
export function isAuthenticated(): boolean {
  if (typeof window === 'undefined') return false;
  return !!(localStorage.getItem("access_token") || localStorage.getItem("firebase_id_token"));
}

/**
 * Clear all auth tokens (for manual logout)
 */
export function clearAuthTokens(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("firebase_id_token");
  }
}

export default authFetch;
