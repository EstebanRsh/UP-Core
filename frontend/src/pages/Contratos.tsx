import { useEffect, useMemo, useState } from "react";
import {
  Button,
  Heading,
  Input,
  Stack,
  Text,
  Card,
  Dialog,
  Table,
  HStack,
} from "@chakra-ui/react";
import {
  listarContratosPaginated,
  crearContrato,
  activarContrato,
  suspenderContrato,
  darDeBajaContrato,
  type Contrato,
} from "../api/contratos";

export default function Contratos() {
  const [items, setItems] = useState<Contrato[]>([]);
  const [nextCursor, setNextCursor] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string>("");

  // Crear
  const [openNew, setOpenNew] = useState(false);
  const [formNew, setFormNew] = useState({
    cliente_id: "",
    plan_id: "",
    direccion_instalacion: "",
    fecha_alta: "",
  });

  const fmt = useMemo(
    () =>
      new Intl.DateTimeFormat("es-AR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      }),
    []
  );

  const cargar = async (cursor: number | null = null) => {
    setLoading(true);
    try {
      const res = await listarContratosPaginated(20, cursor);
      setItems(cursor ? [...items, ...res.contratos] : res.contratos);
      setNextCursor(res.next_cursor);
    } catch (e: any) {
      setMsg(e?.message ?? "Error listando contratos");
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
      const payload = {
        cliente_id: Number(formNew.cliente_id),
        plan_id: Number(formNew.plan_id),
        direccion_instalacion: formNew.direccion_instalacion.trim(),
        fecha_alta: formNew.fecha_alta, // yyyy-mm-dd
      };
      const nuevo = await crearContrato(payload);
      setItems([nuevo, ...items]);
      setOpenNew(false);
      setFormNew({
        cliente_id: "",
        plan_id: "",
        direccion_instalacion: "",
        fecha_alta: "",
      });
      setMsg("Contrato creado con éxito");
    } catch (e: any) {
      setMsg(
        e?.response?.data?.message ?? e?.message ?? "Error al crear contrato"
      );
    }
  };

  // ----- Acciones de estado -----
  const onActivar = async (c: Contrato) => {
    if (!confirm(`¿Activar contrato #${c.id}?`)) return;
    setMsg("");
    try {
      await activarContrato(c.id);
      setItems((prev) =>
        prev.map((it) =>
          it.id === c.id ? { ...it, estado: "activo" as const } : it
        )
      );
      setMsg("Contrato activado");
    } catch (e: any) {
      setMsg(
        e?.response?.data?.message ?? e?.message ?? "Error al activar contrato"
      );
    }
  };

  const onSuspender = async (c: Contrato) => {
    if (!confirm(`¿Suspender contrato #${c.id}?`)) return;
    setMsg("");
    try {
      await suspenderContrato(c.id);
      setItems((prev) =>
        prev.map((it) =>
          it.id === c.id ? { ...it, estado: "suspendido" as const } : it
        )
      );
      setMsg("Contrato suspendido");
    } catch (e: any) {
      // backend devuelve 422 si no está ACTIVO al suspender
      setMsg(
        e?.response?.data?.message ??
          e?.message ??
          "Error al suspender contrato"
      );
    }
  };

  const onBaja = async (c: Contrato) => {
    if (!confirm(`¿Dar de BAJA contrato #${c.id}? Esta acción es definitiva.`))
      return;
    setMsg("");
    try {
      await darDeBajaContrato(c.id);
      setItems((prev) =>
        prev.map((it) =>
          it.id === c.id ? { ...it, estado: "baja" as const } : it
        )
      );
      setMsg("Contrato dado de baja");
    } catch (e: any) {
      setMsg(
        e?.response?.data?.message ??
          e?.message ??
          "Error al dar de baja contrato"
      );
    }
  };

  return (
    <Card.Root>
      <Card.Body>
        <Stack gap={4}>
          <Heading size="md">Contratos</Heading>

          <HStack gap={3} align="center">
            {/* Crear */}
            <Dialog.Root
              open={openNew}
              onOpenChange={(d: any) => setOpenNew(!!d?.open)}
            >
              <Dialog.Trigger asChild>
                <Button onClick={() => setOpenNew(true)}>Nuevo contrato</Button>
              </Dialog.Trigger>

              <Dialog.Backdrop />
              <Dialog.Positioner>
                <Dialog.Content>
                  <Dialog.Header>
                    <Dialog.Title>Crear contrato</Dialog.Title>
                  </Dialog.Header>
                  <form onSubmit={onCrear}>
                    <Stack gap={3} mt={2}>
                      <HStack gap={3}>
                        <Input
                          type="number"
                          placeholder="Cliente ID"
                          value={formNew.cliente_id}
                          onChange={(e) =>
                            setFormNew({
                              ...formNew,
                              cliente_id: e.target.value,
                            })
                          }
                          required
                        />
                        <Input
                          type="number"
                          placeholder="Plan ID"
                          value={formNew.plan_id}
                          onChange={(e) =>
                            setFormNew({ ...formNew, plan_id: e.target.value })
                          }
                          required
                        />
                      </HStack>
                      <Input
                        placeholder="Dirección de instalación"
                        value={formNew.direccion_instalacion}
                        onChange={(e) =>
                          setFormNew({
                            ...formNew,
                            direccion_instalacion: e.target.value,
                          })
                        }
                        required
                      />
                      <Input
                        type="date"
                        value={formNew.fecha_alta}
                        onChange={(e) =>
                          setFormNew({ ...formNew, fecha_alta: e.target.value })
                        }
                        required
                      />

                      <HStack gap={3}>
                        <Button type="submit">Guardar</Button>
                        <Dialog.CloseTrigger asChild>
                          <Button
                            variant="outline"
                            onClick={() => setOpenNew(false)}
                          >
                            Cancelar
                          </Button>
                        </Dialog.CloseTrigger>
                      </HStack>
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
          </HStack>

          {/* Tabla */}
          <Table.Root size="sm" variant="line">
            <Table.Header>
              <Table.Row>
                <Table.ColumnHeader>ID</Table.ColumnHeader>
                <Table.ColumnHeader>Cliente</Table.ColumnHeader>
                <Table.ColumnHeader>Plan</Table.ColumnHeader>
                <Table.ColumnHeader>Estado</Table.ColumnHeader>
                <Table.ColumnHeader>Alta</Table.ColumnHeader>
                <Table.ColumnHeader>Acciones</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {items.map((c) => (
                <Table.Row key={c.id}>
                  <Table.Cell>{c.id}</Table.Cell>
                  <Table.Cell>#{c.cliente_id}</Table.Cell>
                  <Table.Cell>#{c.plan_id}</Table.Cell>
                  <Table.Cell>{c.estado}</Table.Cell>
                  <Table.Cell>
                    {c.fecha_alta ? fmt.format(new Date(c.fecha_alta)) : "-"}
                  </Table.Cell>
                  <Table.Cell>
                    <HStack gap={2}>
                      <Button
                        size="xs"
                        variant="subtle"
                        onClick={() => onActivar(c)}
                        disabled={c.estado === "activo" || c.estado === "baja"}
                      >
                        Activar
                      </Button>
                      <Button
                        size="xs"
                        variant="outline"
                        onClick={() => onSuspender(c)}
                        disabled={c.estado !== "activo"}
                      >
                        Suspender
                      </Button>
                      <Button
                        size="xs"
                        variant="outline"
                        onClick={() => onBaja(c)}
                        disabled={c.estado === "baja"}
                      >
                        Baja
                      </Button>
                    </HStack>
                  </Table.Cell>
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
