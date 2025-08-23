// src/api/metrics.ts
import api from "./client";

type Cliente = { id: number };
type Factura = {
  id: number;
  periodo_mes?: number;
  periodo_anio?: number;
  total?: number;
  estado?: string;
};
type Pago = {
  id: number;
  fecha?: string | null;
  monto?: number;
  metodo?: string;
  estado?: string;
  factura_id?: number;
};

// ---- Totales simples ----
export async function contarClientes(): Promise<number> {
  const { data } = await api.get<Cliente[]>("/clientes/all");
  return Array.isArray(data) ? data.length : 0;
}

export async function contarFacturasMesActual(): Promise<number> {
  const { data } = await api.get<Factura[]>("/facturas/all");
  const hoy = new Date();
  const mes = hoy.getMonth() + 1; // 1..12
  const anio = hoy.getFullYear();
  return (data || []).filter(
    (f) => f.periodo_mes === mes && f.periodo_anio === anio
  ).length;
}

export async function contarPagosHoy(): Promise<number> {
  // /pagos/all a veces trae 'fecha'. Si no, devuelve 0 sin romper.
  const { data } = await api.get<Pago[]>("/pagos/all");
  const hoy = new Date();
  const yyyy = hoy.getFullYear();
  const mm = hoy.getMonth() + 1;
  const dd = hoy.getDate();

  const esHoy = (iso?: string | null) => {
    if (!iso) return false;
    const d = new Date(iso);
    return (
      d.getFullYear() === yyyy &&
      d.getMonth() + 1 === mm &&
      d.getDate() === dd
    );
  };

  return (data || []).filter((p) => esHoy(p.fecha || null)).length;
}

// ---- Listados “últimos N” (se hace client-side con /all) ----
export async function ultimosPagos(limit = 5): Promise<Pago[]> {
  const { data } = await api.get<Pago[]>("/pagos/all");
  const rows = Array.isArray(data) ? data : [];
  return rows.slice(-limit).reverse();
}

export async function ultimasFacturas(limit = 5): Promise<Factura[]> {
  const { data } = await api.get<Factura[]>("/facturas/all");
  const rows = Array.isArray(data) ? data : [];
  return rows.slice(-limit).reverse();
}
