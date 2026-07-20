import { apiClient } from "./apiClient";
import type { DashboardResponse } from "../types/dashboard";

export async function getDashboard(query = "AWC-38"): Promise<DashboardResponse> {
  const response = await apiClient.get<DashboardResponse>("/dashboard", {
    params: { query }
  });

  return response.data;
}
