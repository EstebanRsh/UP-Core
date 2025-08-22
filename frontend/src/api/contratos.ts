import api from "./client";

export type Contrato = {
  id: number;
  cliente_id: number;
  plan_id: number;
  direccion_instalacion: string;
  fecha_alta: string;       // ISO yyyy-mm-dd
  fecha_baja?: string | null;
  estado: "borrador" | "activo" | "suspendido" | "baja";
  fecha_suspension?: string | null;
};

export type ContratosPage = {
  contratos: Contrato[];
  next_cursor: number | null;
};

export async function listarContratosPaginated(
  limit = 20,
  last_seen_id: number | null = null
): Promise<ContratosPage> {
  const { data } = await api.post("/contratos/paginated", { limit, last_seen_id });
  return data;
}

export async function crearContrato(payload: {
  cliente_id: number;
  plan_id: number;
  direccion_instalacion: string;
  fecha_alta: string; // yyyy-mm-dd
}): Promise<Contrato> {
  const { data } = await api.post("/contratos", payload);
  return data;
}
