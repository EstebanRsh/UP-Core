import { IconButton } from "@chakra-ui/react";
import { useColorMode } from "../components/ui/color-mode"; // ajusta ruta

export default function ColorModeToggle() {
  const { colorMode, toggleColorMode } = useColorMode();
  return (
    <IconButton
      aria-label="Cambiar tema"
      variant="ghost"
      size="sm"
      onClick={toggleColorMode}
      title={colorMode === "dark" ? "Cambiar a claro" : "Cambiar a oscuro"}
    >
      {colorMode === "dark" ? "☀️" : "🌙"}
    </IconButton>
  );
}
