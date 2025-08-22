import { Card, Heading, Text } from "@chakra-ui/react";

export default function Home() {
  return (
    <Card.Root>
      <Card.Body>
        <Heading size="md" mb={2}>
          Inicio
        </Heading>
        <Text>
          ✅ Router y layout funcionando. Próximo paso: Login y estructura de
          API.
        </Text>
      </Card.Body>
    </Card.Root>
  );
}
