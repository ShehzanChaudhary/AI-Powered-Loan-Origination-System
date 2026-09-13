import { createContext, useContext, useState, type ReactNode } from "react";
import type { UserRole } from "../types/auth";
import { login as loginApi } from "../api/auth";

interface AuthContextValue {
  token: string | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem("access_token"));
  const [role, setRole] = useState<UserRole | null>(localStorage.getItem("role") as UserRole | null);

  async function login(username: string, password: string) {
    const result = await loginApi(username, password);
    localStorage.setItem("access_token", result.access_token);
    localStorage.setItem("role", result.role);
    setToken(result.access_token);
    setRole(result.role);
  }

  function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("role");
    setToken(null);
    setRole(null);
  }

  return (
    <AuthContext.Provider value={{ token, role, isAuthenticated: !!token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}