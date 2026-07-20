import { apiClient } from "./apiClient";
import type { LoginPayload, RegisterPayload, TokenResponse, User } from "../types/auth";

export async function loginRequest(payload: LoginPayload): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/login", payload);
  return response.data;
}

export async function registerRequest(payload: RegisterPayload): Promise<void> {
  await apiClient.post("/auth/register", payload);
}

export async function getCurrentUserRequest(): Promise<User> {
  const response = await apiClient.get<User>("/auth/me");
  return response.data;
}
