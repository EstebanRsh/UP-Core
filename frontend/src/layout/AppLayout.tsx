import { Box, Container, Flex, Heading, HStack } from "@chakra-ui/react";
import { Link as RouterLink, Outlet } from "react-router-dom";
import ColorModeToggle from "../components/ColorModeToggle";

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  // Usamos RouterLink y estilamos con Chakra vía props inline simples
  return (
    <RouterLink to={to} style={{ textDecoration: "none" }}>
      <Box as="span" _hover={{ color: "brand.500" }}>
        {children}
      </Box>
    </RouterLink>
  );
}

export default function AppLayout() {
  return (
    <Box>
      {/* Topbar */}
      <Box as="header" borderBottomWidth="1px" py={3}>
        <Container maxW="container.xl">
          <Flex align="center" justify="space-between" gap={4}>
            <Heading size="md" color="brand.500">
              UP-Core
            </Heading>
            <HStack gap={6}>
              <NavLink to="/">Inicio</NavLink>
              <NavLink to="/login">Login</NavLink>
              <ColorModeToggle />
            </HStack>
          </Flex>
        </Container>
      </Box>

      {/* Contenido */}
      <Container maxW="container.xl" py={8}>
        <Outlet />
      </Container>
    </Box>
  );
}
