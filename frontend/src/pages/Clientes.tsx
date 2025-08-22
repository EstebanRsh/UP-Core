import { useEffect, useState } from "react";
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
} from "@chakra-ui/react";
import {
  listarClientesPaginated,
  crearCliente,
  actualizarCliente,
  inactivarCliente,
  type Cliente,
} from "../api/clientes";

export default function Clientes() {
  const [items, setItems] = useState<Cliente[]>([]);
  const [nextCursor, setNextCursor] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string>("");

  // Crear
  const [openNew, setOpenNew] = useState(false);
  const [formNew, setFormNew] = useState({
    nombre: "",
    apellido: "",
    documento: "",
    telefono: "",
    email: "",
    direccion: "",
  });

  // Editar
  const [openEdit, setOpenEdit] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [formEdit, setFormEdit] = useState({
    nombre: "",
    apellido: "",
    documento: "",
    telefono: "",
    email: "",
    direccion: "",
  });

  const cargar = async (cursor: number | null = null) => {
    setLoading(true);
    try {
      const res = await listarClientesPaginated(20, cursor);
      setItems(cursor ? [...items, ...res.clientes] : res.clientes);
      setNextCursor(res.next_cursor);
    } catch (e: any) {
      setMsg(e?.message ?? "Error listando clientes");
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
      const nuevo = await crearCliente(formNew);
      setItems([nuevo, ...items]);
      setOpenNew(false);
      setFormNew({
        nombre: "",
        apellido: "",
        documento: "",
        telefono: "",
        email: "",
        direccion: "",
      });
      setMsg("Cliente creado con éxito");
    } catch (e: any) {
      setMsg(
        e?.response?.data?.message ?? e?.message ?? "Error al crear cliente"
      );
    }
  };

  // Preparar edición
  const abrirEditar = (c: Cliente) => {
    setEditId(c.id);
    setFormEdit({
      nombre: c.nombre,
      apellido: c.apellido,
      documento: c.documento,
      telefono: c.telefono ?? "",
      email: c.email ?? "",
      direccion: c.direccion,
    });
    setOpenEdit(true);
  };

  // Guardar edición
  const onEditar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editId) return;
    setMsg("");
    try {
      const actualizado = await actualizarCliente(editId, formEdit);
      setItems((prev) =>
        prev.map((it) => (it.id === actualizado.id ? actualizado : it))
      );
      setOpenEdit(false);
      setEditId(null);
      setMsg("Cliente actualizado con éxito");
    } catch (e: any) {
      setMsg(
        e?.response?.data?.message ??
          e?.message ??
          "Error al actualizar cliente"
      );
    }
  };

  // Inactivar
  const onInactivar = async (c: Cliente) => {
    if (!confirm(`¿Inactivar al cliente ${c.apellido}, ${c.nombre}?`)) return;
    setMsg("");
    try {
      await inactivarCliente(c.id);
      // Refrescamos estado en memoria
      setItems((prev) =>
        prev.map((it) => (it.id === c.id ? { ...it, estado: "inactivo" } : it))
      );
      setMsg("Cliente inactivado");
    } catch (e: any) {
      setMsg(
        e?.response?.data?.message ?? e?.message ?? "Error al inactivar cliente"
      );
    }
  };

  return (
    <Card.Root>
      <Card.Body>
        <Stack gap={4}>
          <Heading size="md">Clientes</Heading>

          <HStack gap={3} align="center">
            {/* Crear */}
            <Dialog.Root
              open={openNew}
              onOpenChange={(detail: any) => setOpenNew(!!detail?.open)}
            >
              <Dialog.Trigger asChild>
                <Button onClick={() => setOpenNew(true)}>Nuevo cliente</Button>
              </Dialog.Trigger>

              <Dialog.Backdrop />
              <Dialog.Positioner>
                <Dialog.Content>
                  <Dialog.Header>
                    <Dialog.Title>Crear cliente</Dialog.Title>
                  </Dialog.Header>
                  <form onSubmit={onCrear}>
                    <Stack gap={3} mt={2}>
                      <Input
                        placeholder="Nombre"
                        value={formNew.nombre}
                        onChange={(e) =>
                          setFormNew({ ...formNew, nombre: e.target.value })
                        }
                        required
                      />
                      <Input
                        placeholder="Apellido"
                        value={formNew.apellido}
                        onChange={(e) =>
                          setFormNew({ ...formNew, apellido: e.target.value })
                        }
                        required
                      />
                      <Input
                        placeholder="Documento"
                        value={formNew.documento}
                        onChange={(e) =>
                          setFormNew({ ...formNew, documento: e.target.value })
                        }
                        required
                      />
                      <Input
                        placeholder="Teléfono"
                        value={formNew.telefono}
                        onChange={(e) =>
                          setFormNew({ ...formNew, telefono: e.target.value })
                        }
                      />
                      <Input
                        placeholder="Email"
                        type="email"
                        value={formNew.email}
                        onChange={(e) =>
                          setFormNew({ ...formNew, email: e.target.value })
                        }
                      />
                      <Input
                        placeholder="Dirección"
                        value={formNew.direccion}
                        onChange={(e) =>
                          setFormNew({ ...formNew, direccion: e.target.value })
                        }
                        required
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
                <Table.ColumnHeader>N°</Table.ColumnHeader>
                <Table.ColumnHeader>Nombre</Table.ColumnHeader>
                <Table.ColumnHeader>Documento</Table.ColumnHeader>
                <Table.ColumnHeader>Estado</Table.ColumnHeader>
                <Table.ColumnHeader>Acciones</Table.ColumnHeader>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {items.map((c) => (
                <Table.Row key={c.id}>
                  <Table.Cell>{c.nro_cliente}</Table.Cell>
                  <Table.Cell>
                    {c.apellido}, {c.nombre}
                  </Table.Cell>
                  <Table.Cell>{c.documento}</Table.Cell>
                  <Table.Cell>{c.estado}</Table.Cell>
                  <Table.Cell>
                    <HStack gap={2}>
                      {/* Editar */}
                      <Dialog.Root
                        open={openEdit && editId === c.id}
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
                            onClick={() => abrirEditar(c)}
                          >
                            Editar
                          </Button>
                        </Dialog.Trigger>
                        <Dialog.Backdrop />
                        <Dialog.Positioner>
                          <Dialog.Content>
                            <Dialog.Header>
                              <Dialog.Title>Editar cliente</Dialog.Title>
                            </Dialog.Header>
                            <form onSubmit={onEditar}>
                              <Stack gap={3} mt={2}>
                                <Input
                                  placeholder="Nombre"
                                  value={formEdit.nombre}
                                  onChange={(e) =>
                                    setFormEdit({
                                      ...formEdit,
                                      nombre: e.target.value,
                                    })
                                  }
                                  required
                                />
                                <Input
                                  placeholder="Apellido"
                                  value={formEdit.apellido}
                                  onChange={(e) =>
                                    setFormEdit({
                                      ...formEdit,
                                      apellido: e.target.value,
                                    })
                                  }
                                  required
                                />
                                <Input
                                  placeholder="Documento"
                                  value={formEdit.documento}
                                  onChange={(e) =>
                                    setFormEdit({
                                      ...formEdit,
                                      documento: e.target.value,
                                    })
                                  }
                                  required
                                />
                                <Input
                                  placeholder="Teléfono"
                                  value={formEdit.telefono}
                                  onChange={(e) =>
                                    setFormEdit({
                                      ...formEdit,
                                      telefono: e.target.value,
                                    })
                                  }
                                />
                                <Input
                                  placeholder="Email"
                                  type="email"
                                  value={formEdit.email}
                                  onChange={(e) =>
                                    setFormEdit({
                                      ...formEdit,
                                      email: e.target.value,
                                    })
                                  }
                                />
                                <Input
                                  placeholder="Dirección"
                                  value={formEdit.direccion}
                                  onChange={(e) =>
                                    setFormEdit({
                                      ...formEdit,
                                      direccion: e.target.value,
                                    })
                                  }
                                  required
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

                      {/* Inactivar */}
                      <Button
                        size="xs"
                        variant="outline"
                        onClick={() => onInactivar(c)}
                        disabled={c.estado === "inactivo"}
                      >
                        Inactivar
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
