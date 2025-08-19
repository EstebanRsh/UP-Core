from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from sqlalchemy.orm import Session
from sqlalchemy import asc

from configs.db import get_db
from auth.roles import require_roles
from models.modelo import (
    Contrato as ContratoModel,
    Cliente as ClienteModel,
    Plan as PlanModel,
    EstadoContratoEnum,
)

Contrato = APIRouter()


class InputContratoCreate(BaseModel):
    cliente_id: int
    plan_id: int
    direccion_instalacion: str
    fecha_alta: Optional[date] = None


class InputContratoUpdate(BaseModel):
    plan_id: Optional[int] = None
    direccion_instalacion: Optional[str] = None
    estado: Optional[EstadoContratoEnum] = None
    fecha_baja: Optional[date] = None
    fecha_suspension: Optional[date] = None


class InputPaginatedRequest(BaseModel):
    limit: int = Field(default=25, ge=1, le=100)
    last_seen_id: Optional[int] = None


def _ensure_exists(db: Session, model, id_: int, nombre: str):
    obj = db.get(model, id_)
    if not obj:
        raise ValueError(f"{nombre} no existe (id={id_})")
    return obj


@Contrato.get("/contratos/hello")
def hello_contratos():
    return "Hello Contratos!!!"


@Contrato.post("/contratos")
def crear_contrato(
    req: Request, body: InputContratoCreate, db: Session = Depends(get_db)
):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        cliente = _ensure_exists(db, ClienteModel, body.cliente_id, "Cliente")
        plan = _ensure_exists(db, PlanModel, body.plan_id, "Plan")
        nuevo = ContratoModel(
            cliente_id=cliente.id,
            plan_id=plan.id,
            direccion_instalacion=body.direccion_instalacion,
            fecha_alta=body.fecha_alta or date.today(),
            estado=EstadoContratoEnum.borrador,
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        return JSONResponse(
            status_code=201,
            content={
                "id": nuevo.id,
                "cliente_id": nuevo.cliente_id,
                "plan_id": nuevo.plan_id,
                "direccion_instalacion": nuevo.direccion_instalacion,
                "fecha_alta": str(nuevo.fecha_alta),
                "estado": nuevo.estado,
            },
        )
    except ValueError as ve:
        db.rollback()
        return JSONResponse(status_code=404, content={"message": str(ve)})
    except Exception as ex:
        db.rollback()
        print("Error crear_contrato ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al crear contrato"}
        )


@Contrato.get("/contratos/all")
def listar_contratos(req: Request, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        rows: List[ContratoModel] = (
            db.query(ContratoModel).order_by(asc(ContratoModel.id)).all()
        )
        salida = [
            {
                "id": c.id,
                "cliente_id": c.cliente_id,
                "plan_id": c.plan_id,
                "direccion_instalacion": c.direccion_instalacion,
                "fecha_alta": str(c.fecha_alta) if c.fecha_alta else None,
                "fecha_baja": str(c.fecha_baja) if c.fecha_baja else None,
                "fecha_suspension": (
                    str(c.fecha_suspension) if c.fecha_suspension else None
                ),
                "estado": c.estado,
            }
            for c in rows
        ]
        return JSONResponse(status_code=200, content=salida)
    except Exception as ex:
        print("Error listar_contratos ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al listar contratos"}
        )


@Contrato.post("/contratos/paginated")
def contratos_paginados(
    req: Request, body: InputPaginatedRequest, db: Session = Depends(get_db)
):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        q = db.query(ContratoModel).order_by(asc(ContratoModel.id))
        if body.last_seen_id is not None:
            q = q.filter(ContratoModel.id > body.last_seen_id)
        rows = q.limit(body.limit).all()
        salida = [
            {
                "id": c.id,
                "cliente_id": c.cliente_id,
                "plan_id": c.plan_id,
                "direccion_instalacion": c.direccion_instalacion,
                "fecha_alta": str(c.fecha_alta) if c.fecha_alta else None,
                "fecha_baja": str(c.fecha_baja) if c.fecha_baja else None,
                "fecha_suspension": (
                    str(c.fecha_suspension) if c.fecha_suspension else None
                ),
                "estado": c.estado,
            }
            for c in rows
        ]
        next_cursor = salida[-1]["id"] if len(salida) == body.limit else None
        return JSONResponse(
            status_code=200, content={"contratos": salida, "next_cursor": next_cursor}
        )
    except Exception as ex:
        print("Error contratos_paginados ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al paginar contratos"}
        )


@Contrato.get("/contratos/{contrato_id}")
def obtener_contrato(contrato_id: int, req: Request, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        c = db.get(ContratoModel, contrato_id)
        if not c:
            return JSONResponse(
                status_code=404, content={"message": "Contrato no encontrado"}
            )
        return JSONResponse(
            status_code=200,
            content={
                "id": c.id,
                "cliente_id": c.cliente_id,
                "plan_id": c.plan_id,
                "direccion_instalacion": c.direccion_instalacion,
                "fecha_alta": str(c.fecha_alta) if c.fecha_alta else None,
                "fecha_baja": str(c.fecha_baja) if c.fecha_baja else None,
                "fecha_suspension": (
                    str(c.fecha_suspension) if c.fecha_suspension else None
                ),
                "estado": c.estado,
            },
        )
    except Exception as ex:
        print("Error obtener_contrato ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al obtener contrato"}
        )


@Contrato.put("/contratos/{contrato_id}")
def actualizar_contrato(
    contrato_id: int,
    body: InputContratoUpdate,
    req: Request,
    db: Session = Depends(get_db),
):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        c = db.get(ContratoModel, contrato_id)
        if not c:
            return JSONResponse(
                status_code=404, content={"message": "Contrato no encontrado"}
            )
        if body.plan_id is not None:
            _ensure_exists(db, PlanModel, body.plan_id, "Plan")
            c.plan_id = body.plan_id
        if body.direccion_instalacion is not None:
            c.direccion_instalacion = body.direccion_instalacion
        if body.estado is not None:
            c.estado = body.estado
        if body.fecha_baja is not None:
            c.fecha_baja = body.fecha_baja
        if body.fecha_suspension is not None:
            c.fecha_suspension = body.fecha_suspension
        db.commit()
        return JSONResponse(
            status_code=200, content={"message": "Contrato actualizado"}
        )
    except ValueError as ve:
        db.rollback()
        return JSONResponse(status_code=404, content={"message": str(ve)})
    except Exception as ex:
        db.rollback()
        print("Error actualizar_contrato ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al actualizar contrato"}
        )


@Contrato.post("/contratos/{contrato_id}/activar")
def activar_contrato(contrato_id: int, req: Request, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        c = db.get(ContratoModel, contrato_id)
        if not c:
            return JSONResponse(
                status_code=404, content={"message": "Contrato no encontrado"}
            )
        c.estado = EstadoContratoEnum.activo
        if not c.fecha_alta:
            c.fecha_alta = date.today()
        db.commit()
        return JSONResponse(status_code=200, content={"message": "Contrato activado"})
    except Exception as ex:
        db.rollback()
        print("Error activar_contrato ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al activar contrato"}
        )


@Contrato.post("/contratos/{contrato_id}/suspender")
def suspender_contrato(contrato_id: int, req: Request, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        c = db.get(ContratoModel, contrato_id)
        if not c:
            return JSONResponse(
                status_code=404, content={"message": "Contrato no encontrado"}
            )
        c.estado = EstadoContratoEnum.suspendido
        c.fecha_suspension = date.today()
        db.commit()
        return JSONResponse(status_code=200, content={"message": "Contrato suspendido"})
    except Exception as ex:
        db.rollback()
        print("Error suspender_contrato ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al suspender contrato"}
        )


@Contrato.post("/contratos/{contrato_id}/baja")
def baja_contrato(contrato_id: int, req: Request, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        c = db.get(ContratoModel, contrato_id)
        if not c:
            return JSONResponse(
                status_code=404, content={"message": "Contrato no encontrado"}
            )
        c.estado = EstadoContratoEnum.baja
        c.fecha_baja = date.today()
        db.commit()
        return JSONResponse(
            status_code=200, content={"message": "Contrato dado de baja"}
        )
    except Exception as ex:
        db.rollback()
        print("Error baja_contrato ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al dar de baja contrato"}
        )
