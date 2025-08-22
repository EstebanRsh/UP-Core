import { Button } from "@chakra-ui/react";
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";

export default function ColorModeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  if (!mounted) return null;

  return (
    <Button
      onClick={() => setTheme(resolvedTheme === "light" ? "dark" : "light")}
    >
      Modo {resolvedTheme === "light" ? "oscuro" : "claro"}
    </Button>
  );
}
