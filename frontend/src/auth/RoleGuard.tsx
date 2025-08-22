import type { ReactElement } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";

type Role = "gerente" | "operador" | "cliente";

type Props = {
  allow: Role[];
  children: ReactElement;
  fallbackTo?: string; // opcional, default "/forbidden"
};

export default function RoleGuard({
  allow,
  children,
  fallbackTo = "/forbidden",
}: Props) {
  const { token, user } = useAuth();
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (!user || !allow.includes(user.role)) {
    return <Navigate to={fallbackTo} replace />;
  }
  return children;
}
