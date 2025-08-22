import { BrowserRouter, Routes, Route } from "react-router-dom";
import AppLayout from "./layout/AppLayout";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Panel from "./pages/Panel";
import ProtectedRoute from "./auth/ProtectedRoute";
import { Text } from "@chakra-ui/react";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />

          <Route
            path="/panel"
            element={
              <ProtectedRoute>
                <Panel />
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Text>404 - Página no encontrada</Text>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
