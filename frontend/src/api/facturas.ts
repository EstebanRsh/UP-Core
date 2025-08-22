import api from "./client";

export type Factura = {
  id: number;
  nro: string;
  contrato_id: number;
  periodo_mes: number;   // 1..12
  periodo_anio: number;  // ej. 2025
  periodo_inicio: string; // ISO
  periodo_fin: string;    // ISO
  subtotal: number;
  mora?: number | null;
  recargo?: number | null;
  total: number;
  estado: "borrador" | "emitida" | "vencida" | "pagada";
  emitida_en?: string | null;
  vencimiento?: string | null;
};

export type FacturasPage = {
  facturas: Factura[];
  next_cursor: number | null;
};

export async function listarFacturasPaginated(
  limit = 20,
  last_seen_id: number | null = null
): Promise<FacturasPage> {
  const { data } = await api.post("/facturas/paginated", { limit, last_seen_id });
  return data;
}

export async function emitirPeriodo(payload: {
  periodo_mes: number;   // 1..12
  periodo_anio: number;  // ej. 2025
}): Promise<{ emitidas: number; message?: string }> {
  const { data } = await api.post("/facturacion/emitir", payload);
  return data;
}
