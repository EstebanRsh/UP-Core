import { Card, CardHeader, CardBody, Heading, Text } from "@chakra-ui/react";

export default function Login() {
  return (
    <Card.Root maxW="md">
      <CardHeader>
        <Heading size="md">Login</Heading>
      </CardHeader>
      <Card.Body>
        <Text>Acá irá el formulario (documento/email + password).</Text>
      </Card.Body>
    </Card.Root>
  );
}
