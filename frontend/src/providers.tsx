import { ChakraProvider } from "@chakra-ui/react";
import { ThemeProvider } from "next-themes";
import { system } from "./system";
import { AuthProvider } from "./auth/AuthContext";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ChakraProvider value={system}>
      <ThemeProvider
        attribute="class"
        defaultTheme="light"
        enableSystem={false}
      >
        <AuthProvider>{children}</AuthProvider>
      </ThemeProvider>
    </ChakraProvider>
  );
}
