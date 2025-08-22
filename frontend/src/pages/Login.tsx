import {
  Card,
  Heading,
  Stack,
  Button,
  Text,
  Input,
  Field,
} from "@chakra-ui/react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{
    type: "success" | "error" | null;
    text: string;
  }>({ type: null, text: "" });
  const navigate = useNavigate();
  const { login } = useAuth();

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatusMsg({ type: null, text: "" });
    try {
      await login(identifier.trim(), password);
      setStatusMsg({ type: "success", text: "Bienvenido" });
      navigate("/");
    } catch (err: any) {
      setStatusMsg({
        type: "error",
        text: err?.message || "Credenciales inválidas",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card.Root maxW="md" mx="auto">
      <Card.Header>
        <Heading size="md">Login</Heading>
      </Card.Header>
      <Card.Body>
        <form onSubmit={onSubmit}>
          <Stack gap={3}>
            <Field.Root required>
              <Field.Label>Documento o Email</Field.Label>
              <Input
                placeholder="30000000001 o gerente@demo.local"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
              />
            </Field.Root>

            <Field.Root required>
              <Field.Label>Contraseña</Field.Label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </Field.Root>

            <Button type="submit" loading={loading}>
              Ingresar
            </Button>

            {statusMsg.type && (
              <Text
                color={statusMsg.type === "error" ? "red.500" : "green.600"}
              >
                {statusMsg.text}
              </Text>
            )}

            <Text color="fg.muted">
              Usá tus credenciales del backend (ej: documento del gerente y
              “secret”).
            </Text>
          </Stack>
        </form>
      </Card.Body>
    </Card.Root>
  );
}
