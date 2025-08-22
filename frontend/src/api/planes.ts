import api from "./client";

export type Plan = {
  id: number;
  nombre: string;
  vel_down: number;       // Mbps
  vel_up: number;         // Mbps
  precio_mensual: number; // ARS
  descripcion?: string | null;
  activo: boolean;
  creado_en: string;
};

export type PlanesPage = {
  planes: Plan[];
  next_cursor: number | null;
};

export async function listarPlanesPaginated(
  limit = 20,
  last_seen_id: number | null = null
): Promise<PlanesPage> {
  const { data } = await api.post("/planes/paginated", { limit, last_seen_id });
  return data;
}

export async function crearPlan(payload: {
  nombre: string;
  vel_down: number;
  vel_up: number;
  precio_mensual: number;
  descripcion?: string;
}): Promise<Plan> {
  const { data } = await api.post("/planes", payload);
  return data;
}

export async function actualizarPlan(
  id: number,
  payload: {
    nombre?: string;
    vel_down?: number;
    vel_up?: number;
    precio_mensual?: number;
    descripcion?: string;
    activo?: boolean; // por si quisieras reactivar
  }
): Promise<Plan> {
  const { data } = await api.put(`/planes/${id}`, payload);
  return data;
}

export async function desactivarPlan(id: number): Promise<{ message: string }> {
  const { data } = await api.delete(`/planes/${id}`);
  return data;
}
