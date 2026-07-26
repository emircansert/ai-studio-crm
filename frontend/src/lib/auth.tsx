"use client";

import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState
} from "react";

import { apiRequest, clearStoredToken, getStoredToken, setStoredToken } from "@/lib/api";
import { entraAcquireToken, entraSignIn, entraSignOut } from "@/lib/entraAuth";
import type { User } from "@/types/api";

/**
 * Authentication is Microsoft Entra ID single sign-on only. The application
 * holds no local credentials, so there is no password sign-in path here.
 */
type AuthContextValue = {
  token: string | null;
  user: User | null;
  isReady: boolean;
  loginWithMicrosoft: () => Promise<void>;
  logout: () => void;
};

// Refresh the Entra ID token well before its ~60 minute expiry.
const ENTRA_TOKEN_REFRESH_MS = 20 * 60 * 1000;

const USER_KEY = "borusan_crm_user";
const AuthContext = createContext<AuthContextValue | null>(null);

function getStoredUser(): User | null {
  if (typeof window === "undefined") {
    return null;
  }
  const value = window.localStorage.getItem(USER_KEY);
  if (!value) {
    return null;
  }
  try {
    return JSON.parse(value) as User;
  } catch {
    window.localStorage.removeItem(USER_KEY);
    return null;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    setToken(getStoredToken());
    setUser(getStoredUser());
    setIsReady(true);
  }, []);

  // Silently refresh the ID token so long-lived sessions do not start failing
  // with 401s when the initial token expires.
  useEffect(() => {
    if (!token) return;
    const timer = window.setInterval(() => {
      entraAcquireToken()
        .then((freshToken) => {
          setStoredToken(freshToken);
          setToken(freshToken);
        })
        .catch(() => undefined);
    }, ENTRA_TOKEN_REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [token]);

  const loginWithMicrosoft = useCallback(async () => {
    const idToken = await entraSignIn();
    setStoredToken(idToken);
    setToken(idToken);
    // The backend provisions/looks up the CRM user from the validated token;
    // /auth/me is the source of truth for role and profile.
    const profile = await apiRequest<User>("/api/v1/auth/me");
    window.localStorage.setItem(USER_KEY, JSON.stringify(profile));
    setUser(profile);
    router.push("/dashboard");
  }, [router]);

  const logout = useCallback(() => {
    clearStoredToken();
    window.localStorage.removeItem(USER_KEY);
    setToken(null);
    setUser(null);
    void entraSignOut();
    router.push("/login");
  }, [router]);

  const value = useMemo(
    () => ({
      token,
      user,
      isReady,
      loginWithMicrosoft,
      logout
    }),
    [isReady, loginWithMicrosoft, logout, token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return value;
}
