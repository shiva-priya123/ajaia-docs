import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import * as authApi from '../api/auth.api';
import type { User } from '../types';
import { TOKEN_KEY } from '../utils/constants';

export interface AuthContextValue {
  user: User | null;
  /** True while we validate a stored token on first load. */
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

function readToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(() => readToken() !== null);

  useEffect(() => {
    if (!readToken()) return;
    let cancelled = false;
    authApi
      .getMe()
      .then((me) => !cancelled && setUser(me))
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
      })
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { token, user: loggedIn } = await authApi.login(email, password);
    localStorage.setItem(TOKEN_KEY, token);
    setUser(loggedIn);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  }, []);

  const value = useMemo(() => ({ user, loading, login, logout }), [user, loading, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
