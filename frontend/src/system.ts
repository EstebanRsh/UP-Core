import { createSystem, defaultConfig, defineConfig } from "@chakra-ui/react";

const config = defineConfig({
  theme: {
    tokens: {
      colors: {
        brand: {
          50:  { value: "#e8f1ff" },
          100: { value: "#cbdfff" },
          200: { value: "#a0c6ff" },
          300: { value: "#74aaff" },
          400: { value: "#4a8dff" },
          500: { value: "#1d4ed8" }, // primario
          600: { value: "#1e3a8a" }, // oscuro
          700: { value: "#1e3a8a" },
          800: { value: "#172554" },
          900: { value: "#0b173d" }
        }
      }
    }
  }
});

export const system = createSystem(defaultConfig, config);
