import { Card, Heading, Text } from "@chakra-ui/react";

export default function Panel() {
  return (
    <Card.Root>
      <Card.Body>
        <Heading size="md" mb={2}>
          Panel
        </Heading>
        <Text>✅ Estás logueado y podés ver esta ruta protegida.</Text>
      </Card.Body>
    </Card.Root>
  );
}
