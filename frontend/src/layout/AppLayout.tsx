import {
  Box,
  Container,
  Flex,
  Heading,
  HStack,
  Button,
} from "@chakra-ui/react";
import { Link as RouterLink, Outlet } from "react-router-dom";
import ColorModeToggle from "../components/ColorModeToggle";
import { useAuth } from "../auth/AuthContext";

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <RouterLink to={to} style={{ textDecoration: "none" }}>
      <Box
        as="span"
        color="link.default"
        _hover={{ color: "link.hover" }}
        fontWeight={500}
      >
        {children}
      </Box>
    </RouterLink>
  );
}

export default function AppLayout() {
  const { token, logout } = useAuth();

  return (
    <Box bg="bg.canvas" minH="100dvh" color="fg.default">
      <Box
        as="header"
        borderBottomWidth="1px"
        borderColor="border.default"
        py={3}
        bg="bg.card"
      >
        <Container maxW="container.xl">
          <Flex align="center" justify="space-between" gap={4}>
            <Heading size="md" color="link.default">
              UP-Core
            </Heading>
            <HStack gap={6}>
              <NavLink to="/">Inicio</NavLink>
              <NavLink to="/login">Login</NavLink>
              {token && <NavLink to="/panel">Panel</NavLink>}
              {token && <NavLink to="/clientes">Clientes</NavLink>}
              {token && <NavLink to="/planes">Planes</NavLink>}
              {token && <NavLink to="/contratos">Contratos</NavLink>}
              {token && <NavLink to="/facturas">Facturas</NavLink>}
              {token && <NavLink to="/pagos">Pagos</NavLink>}
              {token && (
                <Button variant="outline" size="sm" onClick={logout}>
                  Salir
                </Button>
              )}
              <ColorModeToggle />
            </HStack>
          </Flex>
        </Container>
      </Box>

      <Container maxW="container.xl" py={8}>
        <Outlet />
      </Container>
    </Box>
  );
}
