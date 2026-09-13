export type UserRole = "ADMIN" | "LOAN_OFFICER";

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
}

export interface AuthState {
  token: string | null;
  role: UserRole | null;
}