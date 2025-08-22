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
  Box,
  createListCollection,
} from "@chakra-ui/react";
import {
  listarFacturasPaginated,
  emitirPeriodo,
  type Factura,
} from "../api/facturas";

const ESTADOS = ["todos", "borrador", "emitida", "vencida", "pagada"] as const;
type FiltroEstado = (typeof ESTADOS)[number];

export default function Facturas() {
  const [items, setItems] = useState<Factura[]>([]);
  const [nextCursor, setNextCursor] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string>("");

  // Emitir período
  const [openEmit, setOpenEmit] = useState(false);
  const today = new Date();
  const [formEmit, setFormEmit] = useState({
    periodo_mes: String(today.getMonth() + 1),
    periodo_anio: String(today.getFullYear()),
  });

  // Filtro de estado (simple-select controlado)
  const [fEstado, setFEstado] = useState<FiltroEstado>("todos");

  // ✅ Collection para Select v3 (items string → no hace falta itemToString ni getItemValue)
  const estadoCollection = useMemo(
    () =>
      createListCollection({
        items: ESTADOS as unknown as string[], // el Select v3 trabaja con string[]
      }),
    []
  );

  const moneda = useMemo(
    () =>
      new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS" }),
    []
  );
  const fFecha = useMemo(
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
      const res = await listarFacturasPaginated(20, cursor);
      setItems(cursor ? [...items, ...res.facturas] : res.facturas);
      setNextCursor(res.next_cursor);
    } catch (e: any) {
      setMsg(e?.message ?? "Error listando facturas");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargar(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onEmitir = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg("");
    try {
      const payload = {
        periodo_mes: Number(formEmit.periodo_mes),
        periodo_anio: Number(formEmit.periodo_anio),
      };
      const res = await emitirPeriodo(payload);
      setOpenEmit(false);
      await cargar(null);
      setMsg(res?.message || `Facturas emitidas: ${res.emitidas ?? 0}`);
    } catch (e: any) {
      setMsg(
        e?.response?.data?.message ?? e?.message ?? "Error al emitir período"
      );
    }
  };

  const listFiltrada = items.filter((f) =>
    fEstado === "todos" ? true : f.estado === fEstado
  );

  return (
    <Card.Root>
      <Card.Body>
        <Stack gap={4}>
          <Heading size="md">Facturas</Heading>

          <HStack gap={3} align="center" wrap="wrap">
            {/* Emitir período */}
            <Dialog.Root
              open={openEmit}
              onOpenChange={(d: any) => setOpenEmit(!!d?.open)}
            >
              <Dialog.Trigger asChild>
                <Button onClick={() => setOpenEmit(true)}>
                  Emitir período
                </Button>
              </Dialog.Trigger>

              <Dialog.Backdrop />
              <Dialog.Positioner>
                <Dialog.Content>
                  <Dialog.Header>
                    <Dialog.Title>Emitir período</Dialog.Title>
                  </Dialog.Header>
                  <form onSubmit={onEmitir}>
                    <Stack gap={3} mt={2}>
                      <HStack gap={3}>
                        <Input
                          type="number"
                          min={1}
                          max={12}
                          placeholder="Mes (1-12)"
                          value={formEmit.periodo_mes}
                          onChange={(e) =>
                            setFormEmit({
                              ...formEmit,
                              periodo_mes: e.target.value,
                            })
                          }
                          required
                        />
                        <Input
                          type="number"
                          min={2000}
                          max={2100}
                          placeholder="Año (YYYY)"
                          value={formEmit.periodo_anio}
                          onChange={(e) =>
                            setFormEmit({
                              ...formEmit,
                              periodo_anio: e.target.value,
                            })
                          }
                          required
                        />
                      </HStack>

                      <HStack gap={3}>
                        <Button type="submit">Emitir</Button>
                        <Dialog.CloseTrigger asChild>
                          <Button
                            variant="outline"
                            onClick={() => setOpenEmit(false)}
                          >
                            Cancelar
                          </Button>
                        </Dialog.CloseTrigger>
                      </HStack>
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

            {/* Filtro estado — Select v3 con collection */}
            <HStack gap={2} align="center">
              <Box as="span">Estado:</Box>
              <Select.Root
                collection={estadoCollection}
                value={[fEstado]} // simple select → array con un valor
                onValueChange={(details: { value: string[] }) =>
                  setFEstado((details.value[0] ?? "todos") as FiltroEstado)
                }
                size="sm"
              >
                <Select.Trigger width="200px">
                  <Select.ValueText placeholder="Seleccionar estado" />
                </Select.Trigger>
                <Select.Content>
                  {estadoCollection.items.map((item) => (
                    <Select.Item key={item} item={item}>
                      {item}
                    </Select.Item>
                  ))}
                </Select.Content>
              </Select.Root>
            </HStack>
          </HStack>

          {/* Tabla */}
          <Table.Root size="sm" variant="line">
            <Table.Header>
              <Table.Row>
                <Table.ColumnHeader>N°</Table.ColumnHeader>
                <Table.ColumnHeader>Contrato</Table.ColumnHeader>
                <Table.ColumnHeader>Período</Table.ColumnHeader>
                <Table.ColumnHeader>Vencimiento</Table.ColumnHeader>
                <Table.ColumnHeader>Total</Table.ColumnHeader>
                <Table.ColumnHeader>Estado</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {listFiltrada.map((f) => (
                <Table.Row key={f.id}>
                  <Table.Cell>{f.nro}</Table.Cell>
                  <Table.Cell>#{f.contrato_id}</Table.Cell>
                  <Table.Cell>
                    {String(f.periodo_mes).padStart(2, "0")}/{f.periodo_anio}
                  </Table.Cell>
                  <Table.Cell>
                    {f.vencimiento
                      ? fFecha.format(new Date(f.vencimiento))
                      : "-"}
                  </Table.Cell>
                  <Table.Cell>{moneda.format(f.total)}</Table.Cell>
                  <Table.Cell>{f.estado}</Table.Cell>
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
