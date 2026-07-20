export type User = {
  id: number;
  username: string;
  email: string;
  created_at: string;
};

export type LoginPayload = {
  username_or_email: string;
  password: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: "bearer";
  expires_in_minutes: number;
};

export type AuthContextValue = {
  isAuthenticated: boolean;
  isInitializing: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => void;
  refreshAuthState: () => Promise<void>;
  token: string | null;
  user: User | null;
};
