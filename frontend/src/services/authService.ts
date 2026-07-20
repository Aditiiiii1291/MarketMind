import { apiClient } from "./apiClient";
import type { LoginPayload, TokenResponse, User } from "../types/auth";

export async function loginRequest(payload: LoginPayload): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/login", payload);
  return response.data;
}

export async function getCurrentUserRequest(): Promise<User> {
  const response = await apiClient.get<User>("/auth/me");
  return response.data;
}
