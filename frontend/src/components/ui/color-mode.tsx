import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

type ColorMode = "light" | "dark";

export function useColorMode() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const colorMode = (resolvedTheme ?? "light") as ColorMode;
  const toggleColorMode = () =>
    setTheme(colorMode === "light" ? "dark" : "light");
  const setColorMode = (m: ColorMode) => setTheme(m);
  return { colorMode, toggleColorMode, setColorMode, mounted };
}

export function ColorModeButton() {
  const { colorMode, toggleColorMode, mounted } = useColorMode();
  if (!mounted) return null;
  return (
    <button
      aria-label="Cambiar tema"
      title={colorMode === "dark" ? "Cambiar a claro" : "Cambiar a oscuro"}
      onClick={toggleColorMode}
      style={{
        border: "none",
        background: "transparent",
        cursor: "pointer",
        fontSize: 18,
        padding: 6,
      }}
    >
      {colorMode === "dark" ? "☀️" : "🌙"}
    </button>
  );
}
