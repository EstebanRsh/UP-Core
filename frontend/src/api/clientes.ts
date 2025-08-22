import api from "./client";

export type Cliente = {
  id: number;
  nro_cliente: string;
  nombre: string;
  apellido: string;
  documento: string;
  telefono?: string | null;
  email?: string | null;
  direccion: string;
  estado: "activo" | "inactivo";
  creado_en: string;
};

export type ClientesPage = {
  clientes: Cliente[];
  next_cursor: number | null;
};

export async function listarClientesPaginated(limit = 20, last_seen_id: number | null = null): Promise<ClientesPage> {
  const { data } = await api.post("/clientes/paginated", { limit, last_seen_id });
  return data;
}

export async function crearCliente(payload: {
  nombre: string;
  apellido: string;
  documento: string;
  telefono?: string;
  email?: string;
  direccion: string;
}): Promise<Cliente> {
  const { data } = await api.post("/clientes", payload);
  return data;
}
