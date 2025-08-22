import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { login as apiLogin, type LoginResponse } from "../api/auth";

type Role = "gerente" | "operador" | "cliente";
type User = {
  id: number;
  email?: string | null;
  documento?: string | null;
  role: Role;
  activo: boolean;
} | null;

type AuthContextType = {
  token: string | null;
  user: User;
  login: (identifier: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem("token")
  );
  const [user, setUser] = useState<User>(null);

  const login = async (identifier: string, password: string) => {
    const data = await apiLogin(identifier, password);
    if (!data?.token) throw new Error(data?.message || "Login inválido");
    localStorage.setItem("token", data.token);
    setToken(data.token);
    if (data.user) setUser(data.user as User);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  const value = useMemo(() => ({ token, user, login, logout }), [token, user]);

  // (Opcional) acá podríamos llamar a /me si quisieras restaurar user al recargar
  useEffect(() => {}, []);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}
