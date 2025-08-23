// src/pages/Panel.tsx
import { useEffect, useState } from "react";
import {
  Box,
  Grid,
  Heading,
  Table,
  Flex,
  Text,
  Separator,
  Card,
} from "@chakra-ui/react";
import MetricCard from "../components/MetricCard";
import {
  contarClientes,
  contarFacturasMesActual,
  contarPagosHoy,
  ultimasFacturas,
  ultimosPagos,
} from "../api/metrics";

type PagoRow = {
  id: number;
  fecha?: string | null;
  monto?: number;
  metodo?: string;
  estado?: string;
  factura_id?: number;
};

type FacturaRow = {
  id: number;
  nro?: string;
  total?: number;
  estado?: string;
  periodo_mes?: number;
  periodo_anio?: number;
};

export default function Panel() {
  const [loading, setLoading] = useState(true);

  // KPIs
  const [totalClientes, setTotalClientes] = useState<number | undefined>();
  const [facturasMes, setFacturasMes] = useState<number | undefined>();
  const [pagosHoy, setPagosHoy] = useState<number | undefined>();

  // Listas
  const [pagos, setPagos] = useState<PagoRow[]>([]);
  const [facturas, setFacturas] = useState<FacturaRow[]>([]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const [cClientes, cFactMes, cPagosHoy, ultPagos, ultFacts] =
          await Promise.all([
            contarClientes().catch(() => undefined),
            contarFacturasMesActual().catch(() => undefined),
            contarPagosHoy().catch(() => undefined),
            ultimosPagos(5).catch(() => []),
            ultimasFacturas(5).catch(() => []),
          ]);
        if (!mounted) return;
        setTotalClientes(cClientes);
        setFacturasMes(cFactMes);
        setPagosHoy(cPagosHoy);
        setPagos(ultPagos);
        setFacturas(ultFacts);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const hoy = new Date();
  const nombreMes = hoy.toLocaleString("es-AR", { month: "long" });
  const anio = hoy.getFullYear();

  return (
    <Box p="4">
      <Heading size="lg" mb="4">
        Panel general
      </Heading>

      {/* KPIs */}
      <Grid columns={{ base: 1, md: 3 }} gap="4" mb="6" alignItems="stretch">
        <MetricCard
          title="Clientes totales"
          value={totalClientes}
          loading={loading}
          note="Conteo simple de la base."
        />
        <MetricCard
          title={`Facturas de ${nombreMes} ${anio}`}
          value={facturasMes}
          loading={loading}
          note="Cantidad de facturas cuyo período coincide con el mes actual."
        />
        <MetricCard
          title="Pagos de hoy"
          value={pagosHoy}
          loading={loading}
          note="Cantidad de pagos registrados en la fecha local."
        />
      </Grid>

      <Grid columns={{ base: 1, md: 2 }} gap="4">
        {/* Últimos pagos */}
        <Card.Root>
          <Card.Header>
            <Heading size="sm">Últimos pagos</Heading>
          </Card.Header>
          <Card.Body>
            <Table.Root variant="line">
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeader>ID</Table.ColumnHeader>
                  <Table.ColumnHeader>Fecha</Table.ColumnHeader>
                  <Table.ColumnHeader textAlign="right">
                    Monto
                  </Table.ColumnHeader>
                  <Table.ColumnHeader>Método</Table.ColumnHeader>
                  <Table.ColumnHeader>Estado</Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {pagos.map((p) => (
                  <Table.Row key={p.id}>
                    <Table.Cell>{p.id}</Table.Cell>
                    <Table.Cell>
                      {p.fecha
                        ? new Date(p.fecha).toLocaleString("es-AR")
                        : "—"}
                    </Table.Cell>
                    <Table.Cell textAlign="right">
                      {p.monto != null ? p.monto.toFixed(2) : "—"}
                    </Table.Cell>
                    <Table.Cell>{p.metodo ?? "—"}</Table.Cell>
                    <Table.Cell>{p.estado ?? "—"}</Table.Cell>
                  </Table.Row>
                ))}
                {!loading && pagos.length === 0 && (
                  <Table.Row>
                    <Table.Cell colSpan={5}>
                      <Flex justify="center" py="6">
                        <Text color="fg.muted">Sin datos</Text>
                      </Flex>
                    </Table.Cell>
                  </Table.Row>
                )}
              </Table.Body>
            </Table.Root>
          </Card.Body>
        </Card.Root>

        {/* Últimas facturas */}
        <Card.Root>
          <Card.Header>
            <Heading size="sm">Últimas facturas</Heading>
          </Card.Header>
          <Card.Body>
            <Table.Root variant="line">
              <Table.Header>
                <Table.Row>
                  <Table.ColumnHeader>ID</Table.ColumnHeader>
                  <Table.ColumnHeader>Número</Table.ColumnHeader>
                  <Table.ColumnHeader>Período</Table.ColumnHeader>
                  <Table.ColumnHeader>Estado</Table.ColumnHeader>
                  <Table.ColumnHeader textAlign="right">
                    Total
                  </Table.ColumnHeader>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {facturas.map((f) => (
                  <Table.Row key={f.id}>
                    <Table.Cell>{f.id}</Table.Cell>
                    <Table.Cell>{f.nro ?? "—"}</Table.Cell>
                    <Table.Cell>
                      {f.periodo_mes && f.periodo_anio
                        ? `${String(f.periodo_mes).padStart(2, "0")}/${
                            f.periodo_anio
                          }`
                        : "—"}
                    </Table.Cell>
                    <Table.Cell>{f.estado ?? "—"}</Table.Cell>
                    <Table.Cell textAlign="right">
                      {f.total != null ? f.total.toFixed(2) : "—"}
                    </Table.Cell>
                  </Table.Row>
                ))}
                {!loading && facturas.length === 0 && (
                  <Table.Row>
                    <Table.Cell colSpan={5}>
                      <Flex justify="center" py="6">
                        <Text color="fg.muted">Sin datos</Text>
                      </Flex>
                    </Table.Cell>
                  </Table.Row>
                )}
              </Table.Body>
            </Table.Root>
          </Card.Body>
        </Card.Root>
      </Grid>

      <Separator my="6" />
      <Text color="fg.muted" fontSize="sm">
        * Estas métricas se calculan en el cliente consultando endpoints
        existentes (<code>/all</code>). Más adelante podemos moverlas a
        endpoints de métricas en el backend para mejor performance.
      </Text>
    </Box>
  );
}
