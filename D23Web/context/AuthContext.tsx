"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode, useCallback, useRef } from 'react';
import { User, GoogleAuthProvider, signInWithPopup, signOut } from 'firebase/auth';
import { auth } from '@/lib/firebase';
import { useRouter } from 'next/navigation';

interface UserProfile {
  id: string;
  email: string;
  display_name: string | null;
  photo_url: string | null;
  created_at: string;
}

interface AuthContextType {
  currentUser: User | null;
  currentProfile: UserProfile | null;
  loading: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<string | null>;
  idToken: string | null;
  accessToken: string | null;
  refreshToken: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [currentProfile, setCurrentProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [idToken, setIdToken] = useState<string | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const router = useRouter();

  // Use refs to prevent infinite loops
  const isRefreshing = useRef(false);
  const profileFetched = useRef(false);

  const fetchProfile = useCallback(async (token: string) => {
    if (profileFetched.current) return;

    console.log("[Auth] Starting backend authentication...");
    console.log("[Auth] Firebase token (first 50 chars):", token.substring(0, 50));

    try {
      // First authenticate with backend to get our JWT tokens
      const authResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/google`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ firebase_id_token: token }),
      });

      console.log("[Auth] Backend auth response status:", authResponse.status);

      if (!authResponse.ok) {
        const errorText = await authResponse.text();
        console.error("[Auth] Backend auth failed:", errorText);
        throw new Error(`Failed to authenticate with backend: ${errorText}`);
      }

      const authData = await authResponse.json();
      console.log("[Auth] Got JWT tokens from backend");
      console.log("[Auth] access_token (first 50 chars):", authData.access_token?.substring(0, 50));

      setAccessToken(authData.access_token);
      setRefreshToken(authData.refresh_token);

      // Store tokens in localStorage
      if (typeof window !== "undefined") {
        localStorage.setItem("access_token", authData.access_token);
        localStorage.setItem("refresh_token", authData.refresh_token);
        console.log("[Auth] Tokens stored in localStorage");
      }

      // Fetch user profile with the new access token
      const profileResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${authData.access_token}`,
        },
      });

      console.log("[Auth] Profile fetch response status:", profileResponse.status);

      if (!profileResponse.ok) {
        throw new Error('Failed to fetch profile');
      }

      const profileData: UserProfile = await profileResponse.json();
      console.log("[Auth] Profile loaded:", profileData.email);
      setCurrentProfile(profileData);
      profileFetched.current = true;
    } catch (error) {
      console.error("[Auth] Error in fetchProfile:", error);
      setCurrentProfile(null);
      profileFetched.current = false;
    }
  }, []);

  useEffect(() => {
    // Try to restore session from localStorage
    if (typeof window !== "undefined") {
      const storedAccessToken = localStorage.getItem("access_token");
      const storedRefreshToken = localStorage.getItem("refresh_token");
      if (storedAccessToken) {
        setAccessToken(storedAccessToken);
        setRefreshToken(storedRefreshToken);
      }
    }

    let authStateReceived = false;

    // Timeout fallback: if Firebase takes too long to initialize, stop loading
    const loadingTimeout = setTimeout(() => {
      if (!authStateReceived) {
        console.warn("Firebase auth timeout - proceeding without auth");
        setLoading(false);
      }
    }, 5000);

    const unsubscribe = auth.onAuthStateChanged(async (user) => {
      authStateReceived = true;
      clearTimeout(loadingTimeout);
      setCurrentUser(user);
      if (user) {
        try {
          const token = await user.getIdToken();
          setIdToken(token);
          if (typeof window !== "undefined") {
            localStorage.setItem("firebase_id_token", token);
          }
          await fetchProfile(token);
        } catch (error) {
          console.error("Error getting token:", error);
          if ((error as Error).message?.includes('quota-exceeded')) {
            console.warn("Firebase quota exceeded, waiting...");
          }
        }
      } else {
        setIdToken(null);
        setAccessToken(null);
        setRefreshToken(null);
        setCurrentProfile(null);
        profileFetched.current = false;
        if (typeof window !== "undefined") {
          localStorage.removeItem("firebase_id_token");
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
        }
      }
      setLoading(false);
    });

    // Token refresh listener
    const unsubscribeTokenRefresh = auth.onIdTokenChanged(async (user) => {
      if (user && !isRefreshing.current) {
        isRefreshing.current = true;
        try {
          const token = await user.getIdToken(false);
          setIdToken(token);
          if (typeof window !== "undefined") {
            localStorage.setItem("firebase_id_token", token);
          }
        } catch (error) {
          console.error("Error refreshing token:", error);
        } finally {
          isRefreshing.current = false;
        }
      }
    });

    return () => {
      clearTimeout(loadingTimeout);
      unsubscribe();
      unsubscribeTokenRefresh();
    };
  }, [fetchProfile]);

  const login = async () => {
    setLoading(true);
    try {
      const provider = new GoogleAuthProvider();
      await signInWithPopup(auth, provider);
      // onAuthStateChanged will handle setting user and token
    } catch (error) {
      console.error("Error during login:", error);
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      // Logout from backend
      if (refreshToken) {
        try {
          await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/logout`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });
        } catch (error) {
          console.error("Error logging out from backend:", error);
        }
      }

      await signOut(auth);
      setCurrentProfile(null);
      setAccessToken(null);
      setRefreshToken(null);
      profileFetched.current = false;
      if (typeof window !== "undefined") {
        localStorage.removeItem("firebase_id_token");
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      }
      router.push('/');
    } catch (error) {
      console.error("Error during logout:", error);
    } finally {
      setLoading(false);
    }
  };

  // Refresh the backend access token using refresh token
  const refreshAccessToken = useCallback(async (): Promise<string | null> => {
    const currentRefreshToken = refreshToken || (typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null);

    if (!currentRefreshToken) {
      console.log("[Auth] No refresh token available, redirecting to login");
      router.push('/login');
      return null;
    }

    try {
      console.log("[Auth] Attempting to refresh access token...");
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: currentRefreshToken }),
      });

      if (!response.ok) {
        console.error("[Auth] Token refresh failed, status:", response.status);
        // Refresh token is invalid or expired - clear everything and redirect to login
        setAccessToken(null);
        setRefreshToken(null);
        setCurrentProfile(null);
        profileFetched.current = false;
        if (typeof window !== "undefined") {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          localStorage.removeItem("firebase_id_token");
        }
        // Sign out of Firebase too
        try {
          await signOut(auth);
        } catch (e) {
          console.error("[Auth] Error signing out of Firebase:", e);
        }
        router.push('/login');
        return null;
      }

      const data = await response.json();
      console.log("[Auth] Token refresh successful");

      setAccessToken(data.access_token);
      if (data.refresh_token) {
        setRefreshToken(data.refresh_token);
      }

      if (typeof window !== "undefined") {
        localStorage.setItem("access_token", data.access_token);
        if (data.refresh_token) {
          localStorage.setItem("refresh_token", data.refresh_token);
        }
      }

      return data.access_token;
    } catch (error) {
      console.error("[Auth] Error refreshing token:", error);
      router.push('/login');
      return null;
    }
  }, [refreshToken, router]);

  return (
    <AuthContext.Provider value={{
      currentUser,
      currentProfile,
      loading,
      login,
      logout,
      refreshAccessToken,
      idToken,
      accessToken,
      refreshToken,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
