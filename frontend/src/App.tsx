import { BrowserRouter, Routes, Route } from "react-router-dom";
import AppLayout from "./layout/AppLayout";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Panel from "./pages/Panel";
import Clientes from "./pages/Clientes";
import Planes from "./pages/Planes";
import Contratos from "./pages/Contratos";
import Forbidden from "./pages/Forbidden";
import ProtectedRoute from "./auth/ProtectedRoute";
import RoleGuard from "./auth/RoleGuard";
import { Text } from "@chakra-ui/react";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          {/* Panel requiere login + rol gerente u operador */}
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
          import Contratos from "./pages/Contratos"; // ...
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
          <Route path="/forbidden" element={<Forbidden />} />
          <Route path="*" element={<Text>404 - Página no encontrada</Text>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
