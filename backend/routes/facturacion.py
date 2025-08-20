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
    EstadoContratoEnum,
    EstadoFacturaEnum,
)

Facturacion = APIRouter()


class InputGenerarMes(BaseModel):
    anio: Optional[int] = None  # por defecto: hoy
    mes: Optional[int] = Field(default=None, ge=1, le=12)
    emitir: bool = False  # si true, deja en 'emitida'
    dias_vencimiento: int = Field(default=10, ge=1, le=60)


def _month_bounds(anio: int, mes: int) -> tuple[date, date]:
    first = date(anio, mes, 1)
    last_day = calendar.monthrange(anio, mes)[1]
    last = date(anio, mes, last_day)
    return first, last


@Facturacion.get("/facturacion/hello")
def hello_facturacion():
    return "Hello Facturacion!!!"


@Facturacion.post("/facturacion/generar-mes")
def generar_mes(req: Request, body: InputGenerarMes, db: Session = Depends(get_db)):
    """
    Genera facturas del período para TODOS los contratos ACTIVOS.
    Idempotente por la UNIQUE (contrato_id, periodo_anio, periodo_mes).
    """
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard

    today = date.today()
    anio = body.anio or today.year
    mes = body.mes or today.month
    p_ini, p_fin = _month_bounds(anio, mes)

    try:
        contratos: List[ContratoModel] = (
            db.query(ContratoModel)
            .filter(ContratoModel.estado == EstadoContratoEnum.activo)
            .order_by(asc(ContratoModel.id))
            .all()
        )
        creadas = 0
        saltadas = 0
        for c in contratos:
            # ¿Ya existe factura de este período para el contrato?
            ya = (
                db.query(FacturaModel)
                .filter(
                    FacturaModel.contrato_id == c.id,
                    FacturaModel.periodo_anio == anio,
                    FacturaModel.periodo_mes == mes,
                )
                .first()
            )
            if ya:
                saltadas += 1
                continue

            plan = db.get(PlanModel, c.plan_id)
            if not plan or not plan.activo:
                # Si el plan está inactivo, no facturamos (regla simple inicial)
                saltadas += 1
                continue

            subtotal = plan.precio_mensual
            total = subtotal  # sin mora/recargo por ahora
            estado = (
                EstadoFacturaEnum.emitida if body.emitir else EstadoFacturaEnum.borrador
            )

            nueva = FacturaModel(
                nro="PENDIENTE",
                contrato_id=c.id,
                periodo_mes=mes,
                periodo_anio=anio,
                periodo_inicio=p_ini,
                periodo_fin=p_fin,
                subtotal=subtotal,
                total=total,
                estado=estado,
                emitida_en=(
                    datetime.utcnow() if estado == EstadoFacturaEnum.emitida else None
                ),
                vencimiento=(
                    (p_fin + timedelta(days=body.dias_vencimiento))
                    if estado == EstadoFacturaEnum.emitida
                    else None
                ),
                pdf_path=None,
            )
            db.add(nueva)
            db.commit()
            db.refresh(nueva)

            # Numeración definitiva (YYYYMM-ID)
            nueva.nro = f"{anio}{mes:02d}-{nueva.id:06d}"
            db.commit()
            creadas += 1

        return JSONResponse(
            status_code=200,
            content={
                "periodo": f"{anio}-{mes:02d}",
                "contratos_analizados": len(contratos),
                "facturas_creadas": creadas,
                "facturas_existentes_o_saltadas": saltadas,
                "emitidas": body.emitir,
            },
        )
    except Exception as ex:
        db.rollback()
        print("Error generar_mes ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al generar facturación del mes"}
        )
