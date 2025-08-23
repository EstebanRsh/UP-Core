// src/App.tsx
import { Routes, Route, Navigate } from "react-router-dom";
import AppLayout from "./layout/AppLayout";

import Home from "./pages/Home";
import Login from "./pages/Login";
import Panel from "./pages/Panel";
import Clientes from "./pages/Clientes";
import Planes from "./pages/Planes";
import Contratos from "./pages/Contratos";
import Facturas from "./pages/Facturas";
import Pagos from "./pages/Pagos";
import Forbidden from "./pages/Forbidden";

import ProtectedRoute from "./auth/ProtectedRoute";
import RoleGuard from "./auth/RoleGuard";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Home />} />
        <Route path="/login" element={<Login />} />

        <Route
          path="/panel"
          element={
            <ProtectedRoute>
              <RoleGuard allow={["gerente", "operador"]}>
                <Panel />
              </RoleGuard>
            </ProtectedRoute>
          }
        />

        <Route
          path="/clientes"
          element={
            <ProtectedRoute>
              <RoleGuard allow={["gerente", "operador"]}>
                <Clientes />
              </RoleGuard>
            </ProtectedRoute>
          }
        />

        <Route
          path="/planes"
          element={
            <ProtectedRoute>
              <RoleGuard allow={["gerente", "operador"]}>
                <Planes />
              </RoleGuard>
            </ProtectedRoute>
          }
        />

        <Route
          path="/contratos"
          element={
            <ProtectedRoute>
              <RoleGuard allow={["gerente", "operador"]}>
                <Contratos />
              </RoleGuard>
            </ProtectedRoute>
          }
        />

        <Route
          path="/facturas"
          element={
            <ProtectedRoute>
              <RoleGuard allow={["gerente", "operador"]}>
                <Facturas />
              </RoleGuard>
            </ProtectedRoute>
          }
        />

        <Route
          path="/pagos"
          element={
            <ProtectedRoute>
              <RoleGuard allow={["gerente", "operador"]}>
                <Pagos />
              </RoleGuard>
            </ProtectedRoute>
          }
        />

        <Route path="/forbidden" element={<Forbidden />} />
        {/* fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
