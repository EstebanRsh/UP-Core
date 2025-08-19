# backend/routes/cliente.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import asc, func

from configs.db import get_db
from models.modelo import Cliente as ClienteModel, EstadoClienteEnum
from auth.roles import require_roles

Cliente = APIRouter()


# -------- Schemas --------
class InputClienteCreate(BaseModel):
    nombre: str
    apellido: str
    documento: str = Field(max_length=11)  # DNI/CUIT (solo dígitos)
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: str


class InputClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    documento: Optional[str] = Field(default=None, max_length=11)
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None
    estado: Optional[EstadoClienteEnum] = None


class InputPaginatedRequest(BaseModel):
    limit: int = Field(default=25, ge=1, le=100)
    last_seen_id: Optional[int] = None


# ------- Helpers -------
def _norm_doc(doc: Optional[str]) -> Optional[str]:
    if not doc:
        return None
    return "".join(c for c in doc if c.isdigit())


def _next_nro_cliente(db: Session) -> str:
    next_id = (db.query(func.coalesce(func.max(ClienteModel.id), 0)).scalar() or 0) + 1
    return f"{next_id:06d}"


# ------- Rutas -------
@Cliente.get("/clientes/hello")
def hello_cliente():
    return "Hello Cliente!!!"


@Cliente.post("/clientes")
def crear_cliente(
    req: Request, body: InputClienteCreate, db: Session = Depends(get_db)
):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        doc = _norm_doc(body.documento)
        if db.query(ClienteModel).filter(ClienteModel.documento == doc).first():
            return JSONResponse(
                status_code=409, content={"message": "Documento ya registrado"}
            )
        if (
            body.email
            and db.query(ClienteModel)
            .filter(ClienteModel.email == body.email.lower())
            .first()
        ):
            return JSONResponse(
                status_code=409, content={"message": "Email ya registrado"}
            )

        nro = _next_nro_cliente(db)
        nuevo = ClienteModel(
            nro_cliente=nro,
            nombre=body.nombre,
            apellido=body.apellido,
            documento=doc,
            telefono=body.telefono,
            email=body.email.lower() if body.email else None,
            direccion=body.direccion,
            estado=EstadoClienteEnum.activo,
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return JSONResponse(
            status_code=201,
            content={
                "id": nuevo.id,
                "nro_cliente": nuevo.nro_cliente,
                "nombre": nuevo.nombre,
                "apellido": nuevo.apellido,
                "documento": nuevo.documento,
                "telefono": nuevo.telefono,
                "email": nuevo.email,
                "direccion": nuevo.direccion,
                "estado": nuevo.estado,
            },
        )
    except Exception as ex:
        db.rollback()
        print("Error crear_cliente ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al crear cliente"}
        )


@Cliente.get("/clientes/all")
def listar_clientes(req: Request, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        rows: List[ClienteModel] = (
            db.query(ClienteModel).order_by(asc(ClienteModel.id)).all()
        )
        salida = [
            {
                "id": c.id,
                "nro_cliente": c.nro_cliente,
                "nombre": c.nombre,
                "apellido": c.apellido,
                "documento": c.documento,
                "telefono": c.telefono,
                "email": c.email,
                "direccion": c.direccion,
                "estado": c.estado,
                "creado_en": c.creado_en.isoformat() if c.creado_en else None,
            }
            for c in rows
        ]
        return JSONResponse(status_code=200, content=salida)
    except Exception as ex:
        print("Error listar_clientes ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al listar clientes"}
        )


@Cliente.post("/clientes/paginated")
def clientes_paginados(
    req: Request, body: InputPaginatedRequest, db: Session = Depends(get_db)
):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        q = db.query(ClienteModel).order_by(asc(ClienteModel.id))
        if body.last_seen_id is not None:
            q = q.filter(ClienteModel.id > body.last_seen_id)
        rows = q.limit(body.limit).all()
        salida = [
            {
                "id": c.id,
                "nro_cliente": c.nro_cliente,
                "nombre": c.nombre,
                "apellido": c.apellido,
                "documento": c.documento,
                "telefono": c.telefono,
                "email": c.email,
                "direccion": c.direccion,
                "estado": c.estado,
                "creado_en": c.creado_en.isoformat() if c.creado_en else None,
            }
            for c in rows
        ]
        next_cursor = salida[-1]["id"] if len(salida) == body.limit else None
        return JSONResponse(
            status_code=200, content={"clientes": salida, "next_cursor": next_cursor}
        )
    except Exception as ex:
        print("Error clientes_paginados ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al paginar clientes"}
        )


@Cliente.get("/clientes/{cliente_id}")
def obtener_cliente(cliente_id: int, req: Request, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        c = db.get(ClienteModel, cliente_id)
        if not c:
            return JSONResponse(
                status_code=404, content={"message": "Cliente no encontrado"}
            )
        return JSONResponse(
            status_code=200,
            content={
                "id": c.id,
                "nro_cliente": c.nro_cliente,
                "nombre": c.nombre,
                "apellido": c.apellido,
                "documento": c.documento,
                "telefono": c.telefono,
                "email": c.email,
                "direccion": c.direccion,
                "estado": c.estado,
                "creado_en": c.creado_en.isoformat() if c.creado_en else None,
            },
        )
    except Exception as ex:
        print("Error obtener_cliente ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al obtener cliente"}
        )


@Cliente.put("/clientes/{cliente_id}")
def actualizar_cliente(
    cliente_id: int,
    body: InputClienteUpdate,
    req: Request,
    db: Session = Depends(get_db),
):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        c = db.get(ClienteModel, cliente_id)
        if not c:
            return JSONResponse(
                status_code=404, content={"message": "Cliente no encontrado"}
            )

        if body.documento:
            doc = _norm_doc(body.documento)
            exists = (
                db.query(ClienteModel)
                .filter(ClienteModel.documento == doc, ClienteModel.id != cliente_id)
                .first()
            )
            if exists:
                return JSONResponse(
                    status_code=409, content={"message": "Documento ya registrado"}
                )
            c.documento = doc
        if body.email:
            exists = (
                db.query(ClienteModel)
                .filter(
                    ClienteModel.email == body.email.lower(),
                    ClienteModel.id != cliente_id,
                )
                .first()
            )
            if exists:
                return JSONResponse(
                    status_code=409, content={"message": "Email ya registrado"}
                )
            c.email = body.email.lower()

        if body.nombre is not None:
            c.nombre = body.nombre
        if body.apellido is not None:
            c.apellido = body.apellido
        if body.telefono is not None:
            c.telefono = body.telefono
        if body.direccion is not None:
            c.direccion = body.direccion
        if body.estado is not None:
            c.estado = body.estado

        db.commit()
        db.refresh(c)
        return JSONResponse(status_code=200, content={"message": "Cliente actualizado"})
    except Exception as ex:
        db.rollback()
        print("Error actualizar_cliente ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al actualizar cliente"}
        )


@Cliente.delete("/clientes/{cliente_id}")
def eliminar_cliente(cliente_id: int, req: Request, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        c = db.get(ClienteModel, cliente_id)
        if not c:
            return JSONResponse(
                status_code=404, content={"message": "Cliente no encontrado"}
            )
        c.estado = EstadoClienteEnum.inactivo  # baja lógica
        db.commit()
        return JSONResponse(status_code=200, content={"message": "Cliente inactivado"})
    except Exception as ex:
        db.rollback()
        print("Error eliminar_cliente ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al eliminar cliente"}
        )
