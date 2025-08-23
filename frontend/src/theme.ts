import { createSystem, defaultConfig, defineConfig } from "@chakra-ui/react";

const config = defineConfig({
  theme: {
    tokens: {
      colors: {
        brand: {
          50:  { value: "#eff6ff" },
          100: { value: "#dbeafe" },
          200: { value: "#bfdbfe" },
          300: { value: "#93c5fd" },
          400: { value: "#60a5fa" },
          500: { value: "#3b82f6" },
          600: { value: "#2563eb" },
          700: { value: "#1d4ed8" },
          800: { value: "#1e40af" },
          900: { value: "#1e3a8a" },
        },
      },
      radii: {
        xl:  { value: "14px" },
        "2xl": { value: "20px" },
      },
    },
    semanticTokens: {
      colors: {
        "bg.canvas":      { value: { base: "white",        _dark: "gray.950" } },
        "bg.card":        { value: { base: "white",        _dark: "gray.900" } },
        "fg.default":     { value: { base: "gray.800",     _dark: "gray.100" } },
        "fg.muted":       { value: { base: "gray.600",     _dark: "gray.400" } },
        "border.default": { value: { base: "gray.200",     _dark: "gray.800" } },
        "accent.solid":   { value: { base: "{colors.brand.600}", _dark: "{colors.brand.500}" } },
        "accent.subtle":  { value: { base: "{colors.brand.50}",  _dark: "blue.900" } },
        "link.default":   { value: { base: "{colors.brand.600}", _dark: "{colors.brand.400}" } },
        "link.hover":     { value: { base: "{colors.brand.700}", _dark: "{colors.brand.300}" } },
      },
    },
  },
});

export const system = createSystem(defaultConfig, config);
