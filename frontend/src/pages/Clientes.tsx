import { useEffect, useState } from "react";
import {
  Button,
  Heading,
  Input,
  Stack,
  Text,
  Card,
  Dialog,
  Table,
} from "@chakra-ui/react";
import {
  listarClientesPaginated,
  crearCliente,
  type Cliente,
} from "../api/clientes";

export default function Clientes() {
  const [items, setItems] = useState<Cliente[]>([]);
  const [nextCursor, setNextCursor] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  // Dialog crear
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    nombre: "",
    apellido: "",
    documento: "",
    telefono: "",
    email: "",
    direccion: "",
  });
  const [msg, setMsg] = useState<string>("");

  const cargar = async (cursor: number | null = null) => {
    setLoading(true);
    try {
      const res = await listarClientesPaginated(20, cursor);
      setItems(cursor ? [...items, ...res.clientes] : res.clientes);
      setNextCursor(res.next_cursor);
    } catch (e: any) {
      setMsg(e?.message ?? "Error listando clientes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargar(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onCrear = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg("");
    try {
      const nuevo = await crearCliente(form);
      setItems([nuevo, ...items]);
      setOpen(false);
      setForm({
        nombre: "",
        apellido: "",
        documento: "",
        telefono: "",
        email: "",
        direccion: "",
      });
      setMsg("Cliente creado con éxito");
    } catch (e: any) {
      setMsg(
        e?.response?.data?.message ?? e?.message ?? "Error al crear cliente"
      );
    }
  };

  return (
    <Card.Root>
      <Card.Body>
        <Stack gap={4}>
          <Heading size="md">Clientes</Heading>

          <Stack direction="row" gap={3} align="center">
            {/* Dialog v3: namespace */}
            <Dialog.Root
              open={open}
              // onOpenChange entrega { open: boolean }
              onOpenChange={(detail: any) => setOpen(!!detail?.open)}
            >
              <Dialog.Trigger asChild>
                <Button onClick={() => setOpen(true)}>Nuevo cliente</Button>
              </Dialog.Trigger>

              <Dialog.Backdrop />
              <Dialog.Positioner>
                <Dialog.Content>
                  <Dialog.Header>
                    <Dialog.Title>Crear cliente</Dialog.Title>
                  </Dialog.Header>

                  <form onSubmit={onCrear}>
                    <Stack gap={3} mt={2}>
                      <Input
                        placeholder="Nombre"
                        value={form.nombre}
                        onChange={(e) =>
                          setForm({ ...form, nombre: e.target.value })
                        }
                        required
                      />
                      <Input
                        placeholder="Apellido"
                        value={form.apellido}
                        onChange={(e) =>
                          setForm({ ...form, apellido: e.target.value })
                        }
                        required
                      />
                      <Input
                        placeholder="Documento"
                        value={form.documento}
                        onChange={(e) =>
                          setForm({ ...form, documento: e.target.value })
                        }
                        required
                      />
                      <Input
                        placeholder="Teléfono"
                        value={form.telefono}
                        onChange={(e) =>
                          setForm({ ...form, telefono: e.target.value })
                        }
                      />
                      <Input
                        placeholder="Email"
                        type="email"
                        value={form.email}
                        onChange={(e) =>
                          setForm({ ...form, email: e.target.value })
                        }
                      />
                      <Input
                        placeholder="Dirección"
                        value={form.direccion}
                        onChange={(e) =>
                          setForm({ ...form, direccion: e.target.value })
                        }
                        required
                      />
                      <Stack direction="row" gap={3}>
                        <Button type="submit">Guardar</Button>
                        <Dialog.CloseTrigger asChild>
                          <Button
                            variant="outline"
                            onClick={() => setOpen(false)}
                          >
                            Cancelar
                          </Button>
                        </Dialog.CloseTrigger>
                      </Stack>
                      {msg && <Text color="fg.muted">{msg}</Text>}
                    </Stack>
                  </form>
                </Dialog.Content>
              </Dialog.Positioner>
            </Dialog.Root>

            <Button
              variant="outline"
              onClick={() => cargar(null)}
              disabled={loading}
            >
              Refrescar
            </Button>
          </Stack>

          {/* Table v3: namespace */}
          <Table.Root size="sm" variant="line">
            <Table.Header>
              <Table.Row>
                <Table.ColumnHeader>N°</Table.ColumnHeader>
                <Table.ColumnHeader>Nombre</Table.ColumnHeader>
                <Table.ColumnHeader>Documento</Table.ColumnHeader>
                <Table.ColumnHeader>Estado</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {items.map((c) => (
                <Table.Row key={c.id}>
                  <Table.Cell>{c.nro_cliente}</Table.Cell>
                  <Table.Cell>
                    {c.apellido}, {c.nombre}
                  </Table.Cell>
                  <Table.Cell>{c.documento}</Table.Cell>
                  <Table.Cell>{c.estado}</Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table.Root>

          {nextCursor && (
            <Button onClick={() => cargar(nextCursor)} disabled={loading}>
              Cargar más
            </Button>
          )}

          {msg && <Text color="fg.muted">{msg}</Text>}
        </Stack>
      </Card.Body>
    </Card.Root>
  );
}
