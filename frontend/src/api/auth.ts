import { apiClient } from "./client";
import type { TokenResponse } from "../types/auth";

export async function login(username: string, password: string): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/api/v1/auth/login", {
    username,
    password,
  });
  return response.data;
}