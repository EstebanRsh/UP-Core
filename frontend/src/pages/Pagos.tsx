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
  Select,
  createListCollection,
} from "@chakra-ui/react";
import {
  listarPagosPaginated,
  registrarPago,
  descargarRecibo,
  type Pago,
  type MetodoPago,
} from "../api/pagos";

const METODOS: MetodoPago[] = ["efectivo", "transferencia"];

export default function Pagos() {
  const [items, setItems] = useState<Pago[]>([]);
  const [nextCursor, setNextCursor] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string>("");

  // Dialog crear
  const [openNew, setOpenNew] = useState(false);
  const [formNew, setFormNew] = useState({
    factura_id: "",
    monto: "",
    metodo: "efectivo" as MetodoPago,
    referencia: "",
  });

  // Select v3 (collection + value string[])
  const metodoCollection = useMemo(
    () =>
      createListCollection({
        items: METODOS as unknown as string[],
      }),
    []
  );

  const moneda = useMemo(
    () =>
      new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS" }),
    []
  );
  const fFechaHora = useMemo(
    () =>
      new Intl.DateTimeFormat("es-AR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }),
    []
  );

  const cargar = async (cursor: number | null = null) => {
    setLoading(true);
    try {
      const res = await listarPagosPaginated(20, cursor);
      setItems(cursor ? [...items, ...res.pagos] : res.pagos);
      setNextCursor(res.next_cursor);
    } catch (e: any) {
      setMsg(e?.message ?? "Error listando pagos");
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
        factura_id: Number(formNew.factura_id),
        monto: Number(formNew.monto),
        metodo: formNew.metodo,
        referencia: formNew.referencia.trim() || undefined,
      };
      const nuevo = await registrarPago(payload);
      setItems([nuevo, ...items]);
      setOpenNew(false);
      setFormNew({
        factura_id: "",
        monto: "",
        metodo: "efectivo",
        referencia: "",
      });
      setMsg("Pago registrado con éxito");
    } catch (e: any) {
      setMsg(
        e?.response?.data?.message ?? e?.message ?? "Error al registrar pago"
      );
    }
  };

  const onDescargar = async (pago: Pago) => {
    try {
      await descargarRecibo(pago.id);
    } catch (e: any) {
      setMsg(e?.message ?? "Error al descargar recibo");
    }
  };

  return (
    <Card.Root>
      <Card.Body>
        <Stack gap={4}>
          <Heading size="md">Pagos</Heading>

          <HStack gap={3} align="center">
            {/* Registrar pago */}
            <Dialog.Root
              open={openNew}
              onOpenChange={(d: any) => setOpenNew(!!d?.open)}
            >
              <Dialog.Trigger asChild>
                <Button onClick={() => setOpenNew(true)}>Registrar pago</Button>
              </Dialog.Trigger>

              <Dialog.Backdrop />
              <Dialog.Positioner>
                <Dialog.Content>
                  <Dialog.Header>
                    <Dialog.Title>Registrar pago</Dialog.Title>
                  </Dialog.Header>
                  <form onSubmit={onCrear}>
                    <Stack gap={3} mt={2}>
                      <HStack gap={3}>
                        <Input
                          type="number"
                          placeholder="Factura ID"
                          value={formNew.factura_id}
                          onChange={(e) =>
                            setFormNew({
                              ...formNew,
                              factura_id: e.target.value,
                            })
                          }
                          required
                        />
                        <Input
                          type="number"
                          placeholder="Monto"
                          value={formNew.monto}
                          onChange={(e) =>
                            setFormNew({ ...formNew, monto: e.target.value })
                          }
                          required
                        />
                      </HStack>

                      {/* Select v3 para método */}
                      <Select.Root
                        collection={metodoCollection}
                        value={[formNew.metodo]}
                        onValueChange={(details: { value: string[] }) =>
                          setFormNew((f) => ({
                            ...f,
                            metodo:
                              (details.value[0] as MetodoPago) ?? "efectivo",
                          }))
                        }
                        size="sm"
                      >
                        <Select.Label>Método</Select.Label>
                        <Select.Trigger>
                          <Select.ValueText placeholder="Seleccionar método" />
                        </Select.Trigger>
                        <Select.Content>
                          {metodoCollection.items.map((m) => (
                            <Select.Item key={m} item={m}>
                              {m}
                            </Select.Item>
                          ))}
                        </Select.Content>
                      </Select.Root>

                      <Input
                        placeholder="Referencia (opcional: nro de transferencia, etc.)"
                        value={formNew.referencia}
                        onChange={(e) =>
                          setFormNew({ ...formNew, referencia: e.target.value })
                        }
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
                <Table.ColumnHeader>Factura</Table.ColumnHeader>
                <Table.ColumnHeader>Fecha</Table.ColumnHeader>
                <Table.ColumnHeader>Método</Table.ColumnHeader>
                <Table.ColumnHeader>Monto</Table.ColumnHeader>
                <Table.ColumnHeader>Estado</Table.ColumnHeader>
                <Table.ColumnHeader>Acciones</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {items.map((p) => (
                <Table.Row key={p.id}>
                  <Table.Cell>{p.id}</Table.Cell>
                  <Table.Cell>#{p.factura_id}</Table.Cell>
                  <Table.Cell>
                    {p.fecha ? fFechaHora.format(new Date(p.fecha)) : "-"}
                  </Table.Cell>
                  <Table.Cell>{p.metodo}</Table.Cell>
                  <Table.Cell>{moneda.format(p.monto)}</Table.Cell>
                  <Table.Cell>{p.estado}</Table.Cell>
                  <Table.Cell>
                    <HStack gap={2}>
                      <Button
                        size="xs"
                        variant="outline"
                        onClick={() => onDescargar(p)}
                      >
                        Descargar recibo
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
