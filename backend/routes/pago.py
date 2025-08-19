from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from sqlalchemy.orm import Session
from sqlalchemy import asc, func

from configs.db import get_db
from auth.roles import require_roles
from models.modelo import (
    Pago as PagoModel,
    Factura as FacturaModel,
    EstadoPagoEnum,
    MetodoPagoEnum,
    EstadoFacturaEnum,
)

Pago = APIRouter()


class InputPagoCreate(BaseModel):
    factura_id: int
    monto: float = Field(gt=0)
    metodo: MetodoPagoEnum
    referencia: Optional[str] = None
    comprobante_path: Optional[str] = None
    confirmar: bool = True


class InputPaginatedRequest(BaseModel):
    limit: int = Field(default=25, ge=1, le=100)
    last_seen_id: Optional[int] = None


def _float(n):
    return float(n) if n is not None else None


def _recalcular_estado_factura(db: Session, factura: FacturaModel):
    total_pagado = (
        db.query(func.coalesce(func.sum(PagoModel.monto), 0))
        .filter(
            PagoModel.factura_id == factura.id,
            PagoModel.estado != EstadoPagoEnum.anulado,
        )
        .scalar()
        or 0
    )
    if total_pagado >= float(factura.total or 0):
        factura.estado = EstadoFacturaEnum.pagada
    return total_pagado


@Pago.get("/pagos/hello")
def hello_pagos():
    return "Hello Pagos!!!"


@Pago.post("/pagos")
def crear_pago(req: Request, body: InputPagoCreate, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        f = db.get(FacturaModel, body.factura_id)
        if not f:
            return JSONResponse(
                status_code=404, content={"message": "Factura no encontrada"}
            )
        nuevo = PagoModel(
            factura_id=f.id,
            fecha=datetime.utcnow(),
            monto=body.monto,
            metodo=body.metodo,
            referencia=body.referencia,
            comprobante_path=body.comprobante_path,
            estado=(
                EstadoPagoEnum.confirmado
                if body.confirmar
                else EstadoPagoEnum.registrado
            ),
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
        _recalcular_estado_factura(db, f)
        db.commit()
        db.refresh(f)
        return JSONResponse(
            status_code=201,
            content={
                "id": nuevo.id,
                "factura_id": nuevo.factura_id,
                "monto": _float(nuevo.monto),
                "metodo": nuevo.metodo,
                "estado": nuevo.estado,
                "factura_estado": f.estado,
            },
        )
    except Exception as ex:
        db.rollback()
        print("Error crear_pago ---->> ", ex)
        return JSONResponse(status_code=500, content={"message": "Error al crear pago"})


@Pago.get("/pagos/factura/{factura_id}")
def pagos_por_factura(factura_id: int, req: Request, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        rows: List[PagoModel] = (
            db.query(PagoModel)
            .filter(PagoModel.factura_id == factura_id)
            .order_by(asc(PagoModel.id))
            .all()
        )
        out = [
            {
                "id": p.id,
                "fecha": p.fecha.isoformat() if p.fecha else None,
                "monto": _float(p.monto),
                "metodo": p.metodo,
                "estado": p.estado,
                "referencia": p.referencia,
                "comprobante_path": p.comprobante_path,
            }
            for p in rows
        ]
        return JSONResponse(status_code=200, content=out)
    except Exception as ex:
        print("Error pagos_por_factura ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al listar pagos"}
        )


@Pago.get("/pagos/all")
def listar_pagos(req: Request, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        rows: List[PagoModel] = db.query(PagoModel).order_by(asc(PagoModel.id)).all()
        out = [
            {
                "id": p.id,
                "factura_id": p.factura_id,
                "monto": _float(p.monto),
                "metodo": p.metodo,
                "estado": p.estado,
            }
            for p in rows
        ]
        return JSONResponse(status_code=200, content=out)
    except Exception as ex:
        print("Error listar_pagos ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al listar pagos"}
        )


@Pago.post("/pagos/paginated")
def pagos_paginados(
    req: Request, body: InputPaginatedRequest, db: Session = Depends(get_db)
):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        q = db.query(PagoModel).order_by(asc(PagoModel.id))
        if body.last_seen_id is not None:
            q = q.filter(PagoModel.id > body.last_seen_id)
        rows = q.limit(body.limit).all()
        out = [
            {
                "id": p.id,
                "factura_id": p.factura_id,
                "monto": _float(p.monto),
                "metodo": p.metodo,
                "estado": p.estado,
            }
            for p in rows
        ]
        next_cursor = out[-1]["id"] if len(out) == body.limit else None
        return JSONResponse(
            status_code=200, content={"pagos": out, "next_cursor": next_cursor}
        )
    except Exception as ex:
        print("Error pagos_paginados ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al paginar pagos"}
        )
