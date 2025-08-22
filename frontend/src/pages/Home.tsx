import { Card, Heading, Text, Button, Stack } from "@chakra-ui/react";
import { useState } from "react";
import api from "../api/client";

export default function Home() {
  const [ping, setPing] = useState<string>("");

  const probarBackend = async () => {
    try {
      const res = await api.get("/");
      // En tu backend, "/" devuelve "hello world"
      setPing(
        typeof res.data === "string" ? res.data : JSON.stringify(res.data)
      );
    } catch (err: any) {
      setPing(`Error: ${err?.message ?? "desconocido"}`);
    }
  };

  return (
    <Card.Root>
      <Card.Body>
        <Heading size="md" mb={2}>
          Inicio
        </Heading>
        <Text mb={4}>
          ✅ Router y layout funcionando. Próximo paso: Login y estructura de
          API.
        </Text>

        <Stack gap={3} direction={{ base: "column", sm: "row" }}>
          <Button onClick={probarBackend}>Probar backend</Button>
          {ping && <Text>Respuesta: {ping}</Text>}
        </Stack>
      </Card.Body>
    </Card.Root>
  );
}
