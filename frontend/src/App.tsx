import { Container, Box, Heading, Button, Text } from "@chakra-ui/react";
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";

function App() {
  // next-themes: resolvedTheme = "light" | "dark"
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (!mounted) {
    // evita parpadeo de tema en la 1ª pintura
    return (
      <Container maxW="container.sm" py={12}>
        <Text>Cargando UI…</Text>
      </Container>
    );
  }

  const toggle = () => setTheme(resolvedTheme === "light" ? "dark" : "light");

  return (
    <Container maxW="container.md" py={12}>
      <Box display="flex" justifyContent="space-between" alignItems="center">
        <Heading size="lg" color="brand.500">
          UP-Core Frontend
        </Heading>
        <Button onClick={toggle}>
          Modo {resolvedTheme === "light" ? "oscuro" : "claro"}
        </Button>
      </Box>

      <Text mt={6}>✅ Proyecto inicial con Chakra v3 configurado.</Text>
      <Text mt={2} color="fg.muted">
        Hola Core
      </Text>
    </Container>
  );
}

export default App;
