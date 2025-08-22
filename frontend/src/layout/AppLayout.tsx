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
      <Box as="span" _hover={{ color: "brand.500" }}>
        {children}
      </Box>
    </RouterLink>
  );
}

export default function AppLayout() {
  const { token, logout } = useAuth();

  return (
    <Box>
      <Box as="header" borderBottomWidth="1px" py={3}>
        <Container maxW="container.xl">
          <Flex align="center" justify="space-between" gap={4}>
            <Heading size="md" color="brand.500">
              UP-Core
            </Heading>
            <HStack gap={6}>
              <NavLink to="/">Inicio</NavLink>
              <NavLink to="/login">Login</NavLink>
              {token && <NavLink to="/panel">Panel</NavLink>}
              {token && <NavLink to="/clientes">Clientes</NavLink>}
              {token && <NavLink to="/planes">Planes</NavLink>}
              {token && <NavLink to="/contratos">Contratos</NavLink>}

              {token && (
                <Button variant="ghost" onClick={logout}>
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
