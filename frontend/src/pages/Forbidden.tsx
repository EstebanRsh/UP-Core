import { Card, Heading, Text } from "@chakra-ui/react";

export default function Forbidden() {
  return (
    <Card.Root>
      <Card.Body>
        <Heading size="md" mb={2}>
          403 — Acceso denegado
        </Heading>
        <Text>No tenés permisos para ver esta sección.</Text>
      </Card.Body>
    </Card.Root>
  );
}
