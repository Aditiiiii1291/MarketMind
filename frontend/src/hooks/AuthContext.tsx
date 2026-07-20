import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState
} from "react";
import type { ReactNode } from "react";

import {
  getCurrentUserRequest,
  loginRequest,
  registerRequest
} from "../services/authService";
import type {
  AuthContextValue,
  LoginPayload,
  RegisterPayload,
  User
} from "../types/auth";
import { clearStoredToken, getStoredToken, setStoredToken } from "../utils/tokenStorage";

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

type AuthProviderProps = {
  children: ReactNode;
};

export function AuthProvider({ children }: AuthProviderProps) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [user, setUser] = useState<User | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  const logout = useCallback(() => {
    clearStoredToken();
    setToken(null);
    setUser(null);
  }, []);

  const refreshCurrentUser = useCallback(async () => {
    const storedToken = getStoredToken();

    if (!storedToken) {
      setUser(null);
      setToken(null);
      return;
    }

    try {
      const currentUser = await getCurrentUserRequest();
      setToken(storedToken);
      setUser(currentUser);
    } catch (error) {
      logout();
      throw error;
    }
  }, [logout]);

  const login = useCallback(async (payload: LoginPayload) => {
    const tokenResponse = await loginRequest(payload);
    setStoredToken(tokenResponse.access_token);
    setToken(tokenResponse.access_token);
    try {
      const currentUser = await getCurrentUserRequest();
      setUser(currentUser);
    } catch (error) {
      logout();
      throw error;
    }
  }, [logout]);

  const register = useCallback(async (payload: RegisterPayload) => {
    await registerRequest(payload);
  }, []);

  useEffect(() => {
    refreshCurrentUser()
      .catch(() => undefined)
      .finally(() => setIsInitializing(false));
  }, [refreshCurrentUser]);

  useEffect(() => {
    window.addEventListener("marketmind:auth-expired", logout);
    return () => window.removeEventListener("marketmind:auth-expired", logout);
  }, [logout]);

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: Boolean(token),
      isInitializing,
      login,
      logout,
      refreshCurrentUser,
      register,
      token,
      user
    }),
    [isInitializing, login, logout, refreshCurrentUser, register, token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
