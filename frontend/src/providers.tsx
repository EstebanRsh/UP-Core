import { ChakraProvider } from "@chakra-ui/react";
import { ThemeProvider } from "next-themes";
import { system } from "./system";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ChakraProvider value={system}>
      {/* next-themes controla light/dark via clase en <html> */}
      <ThemeProvider
        attribute="class"
        defaultTheme="light"
        enableSystem={false}
      >
        {children}
      </ThemeProvider>
    </ChakraProvider>
  );
}
