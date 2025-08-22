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
  Textarea,
} from "@chakra-ui/react";
import {
  listarPlanesPaginated,
  crearPlan,
  actualizarPlan,
  desactivarPlan,
  type Plan,
} from "../api/planes";

export default function Planes() {
  const [items, setItems] = useState<Plan[]>([]);
  const [nextCursor, setNextCursor] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string>("");

  // Crear
  const [openNew, setOpenNew] = useState(false);
  const [formNew, setFormNew] = useState({
    nombre: "",
    vel_down: "",
    vel_up: "",
    precio_mensual: "",
    descripcion: "",
  });

  // Editar
  const [openEdit, setOpenEdit] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [formEdit, setFormEdit] = useState({
    nombre: "",
    vel_down: "",
    vel_up: "",
    precio_mensual: "",
    descripcion: "",
  });

  const moneda = useMemo(
    () =>
      new Intl.NumberFormat("es-AR", { style: "currency", currency: "ARS" }),
    []
  );

  const cargar = async (cursor: number | null = null) => {
    setLoading(true);
    try {
      const res = await listarPlanesPaginated(20, cursor);
      setItems(cursor ? [...items, ...res.planes] : res.planes);
      setNextCursor(res.next_cursor);
    } catch (e: any) {
      setMsg(e?.message ?? "Error listando planes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargar(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Crear
  const onCrear = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg("");
    try {
      const payload = {
        nombre: formNew.nombre.trim(),
        vel_down: Number(formNew.vel_down),
        vel_up: Number(formNew.vel_up),
        precio_mensual: Number(formNew.precio_mensual),
        descripcion: formNew.descripcion.trim() || undefined,
      };
      const nuevo = await crearPlan(payload);
      setItems([nuevo, ...items]);
      setOpenNew(false);
      setFormNew({
        nombre: "",
        vel_down: "",
        vel_up: "",
        precio_mensual: "",
        descripcion: "",
      });
      setMsg("Plan creado con éxito");
    } catch (e: any) {
      setMsg(e?.response?.data?.message ?? e?.message ?? "Error al crear plan");
    }
  };

  // Preparar edición
  const abrirEditar = (p: Plan) => {
    setEditId(p.id);
    setFormEdit({
      nombre: p.nombre,
      vel_down: String(p.vel_down),
      vel_up: String(p.vel_up),
      precio_mensual: String(p.precio_mensual),
      descripcion: p.descripcion ?? "",
    });
    setOpenEdit(true);
  };

  // Guardar edición
  const onEditar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editId) return;
    setMsg("");
    try {
      const payload = {
        nombre: formEdit.nombre.trim(),
        vel_down: Number(formEdit.vel_down),
        vel_up: Number(formEdit.vel_up),
        precio_mensual: Number(formEdit.precio_mensual),
        descripcion: formEdit.descripcion.trim() || undefined,
      };
      const actualizado = await actualizarPlan(editId, payload);
      setItems((prev) =>
        prev.map((it) => (it.id === actualizado.id ? actualizado : it))
      );
      setOpenEdit(false);
      setEditId(null);
      setMsg("Plan actualizado con éxito");
    } catch (e: any) {
      setMsg(
        e?.response?.data?.message ?? e?.message ?? "Error al actualizar plan"
      );
    }
  };

  // Desactivar
  const onDesactivar = async (p: Plan) => {
    if (!confirm(`¿Desactivar el plan "${p.nombre}"?`)) return;
    setMsg("");
    try {
      await desactivarPlan(p.id);
      setItems((prev) =>
        prev.map((it) => (it.id === p.id ? { ...it, activo: false } : it))
      );
      setMsg("Plan desactivado");
    } catch (e: any) {
      setMsg(
        e?.response?.data?.message ?? e?.message ?? "Error al desactivar plan"
      );
    }
  };

  return (
    <Card.Root>
      <Card.Body>
        <Stack gap={4}>
          <Heading size="md">Planes</Heading>

          <HStack gap={3} align="center">
            {/* Crear */}
            <Dialog.Root
              open={openNew}
              onOpenChange={(detail: any) => setOpenNew(!!detail?.open)}
            >
              <Dialog.Trigger asChild>
                <Button onClick={() => setOpenNew(true)}>Nuevo plan</Button>
              </Dialog.Trigger>

              <Dialog.Backdrop />
              <Dialog.Positioner>
                <Dialog.Content>
                  <Dialog.Header>
                    <Dialog.Title>Crear plan</Dialog.Title>
                  </Dialog.Header>
                  <form onSubmit={onCrear}>
                    <Stack gap={3} mt={2}>
                      <Input
                        placeholder="Nombre del plan"
                        value={formNew.nombre}
                        onChange={(e) =>
                          setFormNew({ ...formNew, nombre: e.target.value })
                        }
                        required
                      />
                      <HStack gap={3}>
                        <Input
                          type="number"
                          placeholder="Vel. bajada (Mbps)"
                          value={formNew.vel_down}
                          onChange={(e) =>
                            setFormNew({ ...formNew, vel_down: e.target.value })
                          }
                          required
                        />
                        <Input
                          type="number"
                          placeholder="Vel. subida (Mbps)"
                          value={formNew.vel_up}
                          onChange={(e) =>
                            setFormNew({ ...formNew, vel_up: e.target.value })
                          }
                          required
                        />
                      </HStack>
                      <Input
                        type="number"
                        placeholder="Precio mensual (ARS)"
                        value={formNew.precio_mensual}
                        onChange={(e) =>
                          setFormNew({
                            ...formNew,
                            precio_mensual: e.target.value,
                          })
                        }
                        required
                      />
                      <Textarea
                        placeholder="Descripción (opcional)"
                        value={formNew.descripcion}
                        onChange={(e) =>
                          setFormNew({
                            ...formNew,
                            descripcion: e.target.value,
                          })
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
                <Table.ColumnHeader>Nombre</Table.ColumnHeader>
                <Table.ColumnHeader>Velocidad</Table.ColumnHeader>
                <Table.ColumnHeader>Precio</Table.ColumnHeader>
                <Table.ColumnHeader>Estado</Table.ColumnHeader>
                <Table.ColumnHeader>Acciones</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {items.map((p) => (
                <Table.Row key={p.id}>
                  <Table.Cell>{p.nombre}</Table.Cell>
                  <Table.Cell>
                    ↓ {p.vel_down} / ↑ {p.vel_up} Mbps
                  </Table.Cell>
                  <Table.Cell>{moneda.format(p.precio_mensual)}</Table.Cell>
                  <Table.Cell>{p.activo ? "activo" : "inactivo"}</Table.Cell>
                  <Table.Cell>
                    <HStack gap={2}>
                      {/* Editar */}
                      <Dialog.Root
                        open={openEdit && editId === p.id}
                        onOpenChange={(detail: any) => {
                          const isOpen = !!detail?.open;
                          setOpenEdit(isOpen);
                          if (!isOpen) setEditId(null);
                        }}
                      >
                        <Dialog.Trigger asChild>
                          <Button
                            size="xs"
                            variant="subtle"
                            onClick={() => abrirEditar(p)}
                          >
                            Editar
                          </Button>
                        </Dialog.Trigger>
                        <Dialog.Backdrop />
                        <Dialog.Positioner>
                          <Dialog.Content>
                            <Dialog.Header>
                              <Dialog.Title>Editar plan</Dialog.Title>
                            </Dialog.Header>
                            <form onSubmit={onEditar}>
                              <Stack gap={3} mt={2}>
                                <Input
                                  placeholder="Nombre del plan"
                                  value={formEdit.nombre}
                                  onChange={(e) =>
                                    setFormEdit({
                                      ...formEdit,
                                      nombre: e.target.value,
                                    })
                                  }
                                  required
                                />
                                <HStack gap={3}>
                                  <Input
                                    type="number"
                                    placeholder="Vel. bajada (Mbps)"
                                    value={formEdit.vel_down}
                                    onChange={(e) =>
                                      setFormEdit({
                                        ...formEdit,
                                        vel_down: e.target.value,
                                      })
                                    }
                                    required
                                  />
                                  <Input
                                    type="number"
                                    placeholder="Vel. subida (Mbps)"
                                    value={formEdit.vel_up}
                                    onChange={(e) =>
                                      setFormEdit({
                                        ...formEdit,
                                        vel_up: e.target.value,
                                      })
                                    }
                                    required
                                  />
                                </HStack>
                                <Input
                                  type="number"
                                  placeholder="Precio mensual (ARS)"
                                  value={formEdit.precio_mensual}
                                  onChange={(e) =>
                                    setFormEdit({
                                      ...formEdit,
                                      precio_mensual: e.target.value,
                                    })
                                  }
                                  required
                                />
                                <Textarea
                                  placeholder="Descripción (opcional)"
                                  value={formEdit.descripcion}
                                  onChange={(e) =>
                                    setFormEdit({
                                      ...formEdit,
                                      descripcion: e.target.value,
                                    })
                                  }
                                />

                                <HStack gap={3}>
                                  <Button type="submit">Guardar</Button>
                                  <Dialog.CloseTrigger asChild>
                                    <Button
                                      variant="outline"
                                      onClick={() => setOpenEdit(false)}
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

                      {/* Desactivar */}
                      <Button
                        size="xs"
                        variant="outline"
                        onClick={() => onDesactivar(p)}
                        disabled={!p.activo}
                      >
                        Desactivar
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
