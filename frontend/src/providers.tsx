import { ChakraProvider } from "@chakra-ui/react";
import { ThemeProvider } from "next-themes";
import { system } from "./theme";
import { AuthProvider } from "./auth/AuthContext";

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ChakraProvider value={system}>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
        <AuthProvider>{children}</AuthProvider>
      </ThemeProvider>
    </ChakraProvider>
  );
}
