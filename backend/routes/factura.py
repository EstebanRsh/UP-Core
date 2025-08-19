from datetime import date, datetime, timedelta
import calendar
from typing import Optional, List

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from sqlalchemy.orm import Session
from sqlalchemy import asc

from configs.db import get_db
from auth.roles import require_roles
from models.modelo import (
    Factura as FacturaModel,
    Contrato as ContratoModel,
    Plan as PlanModel,
    EstadoFacturaEnum,
)

Factura = APIRouter()


class InputFacturaCreate(BaseModel):
    contrato_id: int
    periodo_mes: int = Field(ge=1, le=12)
    periodo_anio: int = Field(ge=2000, le=2100)
    periodo_inicio: Optional[date] = None
    periodo_fin: Optional[date] = None
    mora: Optional[float] = None
    recargo: Optional[float] = None
    pdf_path: Optional[str] = None


class InputFacturaUpdate(BaseModel):
    mora: Optional[float] = None
    recargo: Optional[float] = None
    pdf_path: Optional[str] = None
    estado: Optional[EstadoFacturaEnum] = None
    vencimiento: Optional[date] = None


class InputPaginatedRequest(BaseModel):
    limit: int = Field(default=25, ge=1, le=100)
    last_seen_id: Optional[int] = None


class InputEmitir(BaseModel):
    vencimiento: Optional[date] = None


def _month_bounds(anio: int, mes: int) -> tuple[date, date]:
    first = date(anio, mes, 1)
    last_day = calendar.monthrange(anio, mes)[1]
    last = date(anio, mes, last_day)
    return first, last


def _float(n):
    return float(n) if n is not None else None


@Factura.get("/facturas/hello")
def hello_facturas():
    return "Hello Facturas!!!"


@Factura.post("/facturas")
def crear_factura(
    req: Request, body: InputFacturaCreate, db: Session = Depends(get_db)
):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        contrato = db.get(ContratoModel, body.contrato_id)
        if not contrato:
            return JSONResponse(
                status_code=404, content={"message": "Contrato no encontrado"}
            )
        plan = db.get(PlanModel, contrato.plan_id)
        if not plan:
            return JSONResponse(
                status_code=404, content={"message": "Plan del contrato no encontrado"}
            )
        dup = (
            db.query(FacturaModel)
            .filter(
                FacturaModel.contrato_id == body.contrato_id,
                FacturaModel.periodo_mes == body.periodo_mes,
                FacturaModel.periodo_anio == body.periodo_anio,
            )
            .first()
        )
        if dup:
            return JSONResponse(
                status_code=409,
                content={"message": "Ya existe factura para ese contrato y período"},
            )

        p_ini, p_fin = (body.periodo_inicio, body.periodo_fin)
        if not p_ini or not p_fin:
            p_ini, p_fin = _month_bounds(body.periodo_anio, body.periodo_mes)

        subtotal = plan.precio_mensual
        mora = body.mora or 0
        recargo = body.recargo or 0
        total = (subtotal or 0) + mora + recargo

        nueva = FacturaModel(
            nro="PENDIENTE",
            contrato_id=contrato.id,
            periodo_mes=body.periodo_mes,
            periodo_anio=body.periodo_anio,
            periodo_inicio=p_ini,
            periodo_fin=p_fin,
            subtotal=subtotal,
            mora=mora or None,
            recargo=recargo or None,
            total=total,
            estado=EstadoFacturaEnum.borrador,
            vencimiento=None,
            pdf_path=body.pdf_path,
        )
        db.add(nueva)
        db.commit()
        db.refresh(nueva)

        nueva.nro = f"{nueva.periodo_anio}{nueva.periodo_mes:02d}-{nueva.id:06d}"
        db.commit()
        db.refresh(nueva)

        return JSONResponse(
            status_code=201,
            content={
                "id": nueva.id,
                "nro": nueva.nro,
                "contrato_id": nueva.contrato_id,
                "periodo_mes": nueva.periodo_mes,
                "periodo_anio": nueva.periodo_anio,
                "periodo_inicio": str(nueva.periodo_inicio),
                "periodo_fin": str(nueva.periodo_fin),
                "subtotal": _float(nueva.subtotal),
                "mora": _float(nueva.mora),
                "recargo": _float(nueva.recargo),
                "total": _float(nueva.total),
                "estado": nueva.estado,
                "emitida_en": None,
                "vencimiento": None,
                "pdf_path": nueva.pdf_path,
            },
        )
    except Exception as ex:
        db.rollback()
        print("Error crear_factura ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al crear factura"}
        )


@Factura.get("/facturas/all")
def listar_facturas(req: Request, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        rows: List[FacturaModel] = (
            db.query(FacturaModel).order_by(asc(FacturaModel.id)).all()
        )
        out = [
            {
                "id": f.id,
                "nro": f.nro,
                "contrato_id": f.contrato_id,
                "periodo_mes": f.periodo_mes,
                "periodo_anio": f.periodo_anio,
                "periodo_inicio": str(f.periodo_inicio),
                "periodo_fin": str(f.periodo_fin),
                "subtotal": _float(f.subtotal),
                "mora": _float(f.mora),
                "recargo": _float(f.recargo),
                "total": _float(f.total),
                "estado": f.estado,
                "emitida_en": f.emitida_en.isoformat() if f.emitida_en else None,
                "vencimiento": str(f.vencimiento) if f.vencimiento else None,
                "pdf_path": f.pdf_path,
            }
            for f in rows
        ]
        return JSONResponse(status_code=200, content=out)
    except Exception as ex:
        print("Error listar_facturas ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al listar facturas"}
        )


@Factura.post("/facturas/paginated")
def facturas_paginadas(
    req: Request, body: InputPaginatedRequest, db: Session = Depends(get_db)
):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        q = db.query(FacturaModel).order_by(asc(FacturaModel.id))
        if body.last_seen_id is not None:
            q = q.filter(FacturaModel.id > body.last_seen_id)
        rows = q.limit(body.limit).all()
        out = [
            {
                "id": f.id,
                "nro": f.nro,
                "contrato_id": f.contrato_id,
                "periodo_mes": f.periodo_mes,
                "periodo_anio": f.periodo_anio,
                "total": _float(f.total),
                "estado": f.estado,
            }
            for f in rows
        ]
        next_cursor = out[-1]["id"] if len(out) == body.limit else None
        return JSONResponse(
            status_code=200, content={"facturas": out, "next_cursor": next_cursor}
        )
    except Exception as ex:
        print("Error facturas_paginadas ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al paginar facturas"}
        )


@Factura.get("/facturas/{factura_id}")
def obtener_factura(factura_id: int, req: Request, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        f = db.get(FacturaModel, factura_id)
        if not f:
            return JSONResponse(
                status_code=404, content={"message": "Factura no encontrada"}
            )
        return JSONResponse(
            status_code=200,
            content={
                "id": f.id,
                "nro": f.nro,
                "contrato_id": f.contrato_id,
                "periodo_mes": f.periodo_mes,
                "periodo_anio": f.periodo_anio,
                "periodo_inicio": str(f.periodo_inicio),
                "periodo_fin": str(f.periodo_fin),
                "subtotal": _float(f.subtotal),
                "mora": _float(f.mora),
                "recargo": _float(f.recargo),
                "total": _float(f.total),
                "estado": f.estado,
                "emitida_en": f.emitida_en.isoformat() if f.emitida_en else None,
                "vencimiento": str(f.vencimiento) if f.vencimiento else None,
                "pdf_path": f.pdf_path,
            },
        )
    except Exception as ex:
        print("Error obtener_factura ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al obtener factura"}
        )


@Factura.put("/facturas/{factura_id}")
def actualizar_factura(
    factura_id: int,
    body: InputFacturaUpdate,
    req: Request,
    db: Session = Depends(get_db),
):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        f = db.get(FacturaModel, factura_id)
        if not f:
            return JSONResponse(
                status_code=404, content={"message": "Factura no encontrada"}
            )
        changed = False
        if body.mora is not None:
            f.mora = body.mora
            changed = True
        if body.recargo is not None:
            f.recargo = body.recargo
            changed = True
        if body.pdf_path is not None:
            f.pdf_path = body.pdf_path
            changed = True
        if body.vencimiento is not None:
            f.vencimiento = body.vencimiento
            changed = True
        if body.estado is not None:
            f.estado = body.estado
            changed = True
        if changed:
            f.total = (f.subtotal or 0) + (f.mora or 0) + (f.recargo or 0)
            db.commit()
        return JSONResponse(status_code=200, content={"message": "Factura actualizada"})
    except Exception as ex:
        db.rollback()
        print("Error actualizar_factura ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al actualizar factura"}
        )


@Factura.post("/facturas/{factura_id}/emitir")
def emitir_factura(
    factura_id: int, body: InputEmitir, req: Request, db: Session = Depends(get_db)
):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        f = db.get(FacturaModel, factura_id)
        if not f:
            return JSONResponse(
                status_code=404, content={"message": "Factura no encontrada"}
            )
        f.estado = EstadoFacturaEnum.emitida
        f.emitida_en = datetime.utcnow()
        f.vencimiento = body.vencimiento or (f.periodo_fin + timedelta(days=10))
        db.commit()
        return JSONResponse(status_code=200, content={"message": "Factura emitida"})
    except Exception as ex:
        db.rollback()
        print("Error emitir_factura ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al emitir factura"}
        )


@Factura.get("/contratos/{contrato_id}/facturas")
def facturas_por_contrato(
    contrato_id: int, req: Request, db: Session = Depends(get_db)
):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        rows = (
            db.query(FacturaModel)
            .filter(FacturaModel.contrato_id == contrato_id)
            .order_by(asc(FacturaModel.id))
            .all()
        )
        out = [
            {
                "id": f.id,
                "nro": f.nro,
                "total": _float(f.total),
                "estado": f.estado,
                "periodo": f"{f.periodo_anio}-{f.periodo_mes:02d}",
            }
            for f in rows
        ]
        return JSONResponse(status_code=200, content=out)
    except Exception as ex:
        print("Error facturas_por_contrato ---->> ", ex)
        return JSONResponse(
            status_code=500,
            content={"message": "Error al listar facturas del contrato"},
        )
