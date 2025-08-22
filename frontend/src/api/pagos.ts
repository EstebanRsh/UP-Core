import api from "./client";

export type MetodoPago = "efectivo" | "transferencia";
export type EstadoPago = "registrado" | "confirmado" | "anulado";

export type Pago = {
  id: number;
  factura_id: number;
  fecha: string; // ISO
  monto: number;
  metodo: MetodoPago;
  referencia?: string | null;
  comprobante_path?: string | null;
  estado: EstadoPago;
};

export type PagosPage = {
  pagos: Pago[];
  next_cursor: number | null;
};

export async function listarPagosPaginated(
  limit = 20,
  last_seen_id: number | null = null
): Promise<PagosPage> {
  const { data } = await api.post("/pagos/paginated", { limit, last_seen_id });
  return data;
}

export async function registrarPago(payload: {
  factura_id: number;
  monto: number;
  metodo: MetodoPago;
  referencia?: string;
}): Promise<Pago> {
  const { data } = await api.post("/pagos", payload);
  return data;
}

/** Descarga el PDF del recibo del pago indicado */
export async function descargarRecibo(pagoId: number): Promise<void> {
  const res = await api.get(`/pagos/${pagoId}/recibo`, { responseType: "blob" });

  // Intentar recuperar el nombre de archivo del header (opcional)
  let filename = `recibo_pago_${pagoId}.pdf`;
  const dispo = (res.headers as any)["content-disposition"] as string | undefined;
  if (dispo) {
    const m = /filename\*?=(?:UTF-8'')?["']?([^"';]+)["']?/.exec(dispo);
    if (m?.[1]) filename = decodeURIComponent(m[1]);
  }

  const blob = new Blob([res.data], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
