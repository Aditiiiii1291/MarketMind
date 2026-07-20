import {
  createContext,
  ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState
} from "react";

import { getCurrentUserRequest, loginRequest } from "../services/authService";
import type { AuthContextValue, LoginPayload, User } from "../types/auth";
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

  const refreshAuthState = useCallback(async () => {
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
    } catch {
      logout();
    }
  }, [logout]);

  const login = useCallback(async (payload: LoginPayload) => {
    const tokenResponse = await loginRequest(payload);
    setStoredToken(tokenResponse.access_token);
    setToken(tokenResponse.access_token);
    const currentUser = await getCurrentUserRequest();
    setUser(currentUser);
  }, []);

  useEffect(() => {
    refreshAuthState().finally(() => setIsInitializing(false));
  }, [refreshAuthState]);

  const value = useMemo<AuthContextValue>(
    () => ({
      isAuthenticated: Boolean(token),
      isInitializing,
      login,
      logout,
      refreshAuthState,
      token,
      user
    }),
    [isInitializing, login, logout, refreshAuthState, token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
