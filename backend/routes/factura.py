from datetime import date, datetime, timedelta
import calendar
from typing import Optional, List
import os
from pathlib import Path

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

from sqlalchemy.orm import Session
from sqlalchemy import asc

from configs.db import get_db
from auth.roles import require_roles, require_owner_or_roles
from models.modelo import (
    Factura as FacturaModel,
    Contrato as ContratoModel,
    Plan as PlanModel,
    Cliente as ClienteModel,
    EstadoFacturaEnum,
)

# --------- PDF (reportlab) ---------
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm

    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

Factura = APIRouter()


# =========================================================
# Schemas
# =========================================================
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
    dias_vencimiento: int = Field(default=10, ge=1, le=60)


# =========================================================
# Helpers
# =========================================================
def _month_bounds(anio: int, mes: int) -> tuple[date, date]:
    first = date(anio, mes, 1)
    last_day = calendar.monthrange(anio, mes)[1]
    last = date(anio, mes, last_day)
    return first, last


def _float(n):
    return float(n) if n is not None else None


def _storage_root() -> Path:
    return Path(__file__).resolve().parent.parent / "storage"


def _pdf_path_for(f: FacturaModel) -> Path:
    # storage/facturas/YYYY/MM/factura_000123.pdf
    base = _storage_root() / "facturas" / f"{f.periodo_anio}" / f"{f.periodo_mes:02d}"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"factura_{f.id:06d}.pdf"


def _render_factura_pdf(
    path: Path, f: FacturaModel, c: ContratoModel, cli: ClienteModel, p: PlanModel
):
    if not REPORTLAB_OK:
        raise RuntimeError("reportlab no está instalado")
    w, h = A4
    can = canvas.Canvas(str(path), pagesize=A4)
    x_margin = 20 * mm
    y = h - 20 * mm

    # Encabezado
    can.setFont("Helvetica-Bold", 14)
    can.drawString(x_margin, y, "ISP Manager — Factura")
    can.setFont("Helvetica", 10)
    y -= 14
    can.drawString(x_margin, y, f"Nro: {f.nro or 'PENDIENTE'}")
    y -= 12
    can.drawString(
        x_margin,
        y,
        f"Fecha emisión: {f.emitida_en.isoformat() if f.emitida_en else '-'}",
    )
    y -= 12
    can.drawString(
        x_margin,
        y,
        f"Vencimiento: {f.vencimiento.isoformat() if f.vencimiento else '-'}",
    )

    # Cliente
    y -= 20
    can.setFont("Helvetica-Bold", 12)
    can.drawString(x_margin, y, "Cliente")
    can.setFont("Helvetica", 10)
    y -= 14
    can.drawString(x_margin, y, f"{cli.apellido}, {cli.nombre} — Doc: {cli.documento}")
    y -= 12
    can.drawString(x_margin, y, f"Dirección: {cli.direccion}")
    y -= 12
    can.drawString(x_margin, y, f"Email: {cli.email or '-'} Tel: {cli.telefono or '-'}")

    # Contrato / Plan
    y -= 20
    can.setFont("Helvetica-Bold", 12)
    can.drawString(x_margin, y, "Contrato / Plan")
    can.setFont("Helvetica", 10)
    y -= 14
    can.drawString(
        x_margin,
        y,
        f"Contrato ID: {c.id} — Dirección instalación: {c.direccion_instalacion}",
    )
    y -= 12
    can.drawString(
        x_margin,
        y,
        f"Plan: {p.nombre} ({p.vel_down}/{p.vel_up} Mbps) — Precio: ${_float(p.precio_mensual):,.2f}",
    )

    # Período
    y -= 20
    can.setFont("Helvetica-Bold", 12)
    can.drawString(x_margin, y, "Período")
    can.setFont("Helvetica", 10)
    y -= 14
    can.drawString(
        x_margin,
        y,
        f"{f.periodo_anio}-{f.periodo_mes:02d}  [{f.periodo_inicio}  a  {f.periodo_fin}]",
    )

    # Totales
    y -= 20
    can.setFont("Helvetica-Bold", 12)
    can.drawString(x_margin, y, "Detalle")
    can.setFont("Helvetica", 10)
    y -= 14
    can.drawString(x_margin, y, f"Subtotal: ${_float(f.subtotal):,.2f}")
    y -= 12
    can.drawString(x_margin, y, f"Mora:     ${_float(f.mora or 0):,.2f}")
    y -= 12
    can.drawString(x_margin, y, f"Recargo:  ${_float(f.recargo or 0):,.2f}")
    y -= 14
    can.setFont("Helvetica-Bold", 12)
    can.drawString(x_margin, y, f"TOTAL:    ${_float(f.total):,.2f}")

    # Pie
    y -= 24
    can.setFont("Helvetica", 9)
    can.drawString(
        x_margin,
        y,
        "Medios de pago: Transferencia / Efectivo. Adjunte comprobante en el portal de pagos.",
    )
    y -= 12
    can.drawString(x_margin, y, "Gracias por su preferencia.")

    can.showPage()
    can.save()


# =========================================================
# Rutas
# =========================================================
@Factura.get("/facturas/hello")
def hello_facturas():
    return "Hello Facturas!!!"


@Factura.get("/mi/facturas")
def mis_facturas(req: Request, db: Session = Depends(get_db)):
    guard, cliente_id = require_owner_or_roles(req.headers, db, allowed_roles=None)
    if guard:
        return guard
    rows: List[FacturaModel] = (
        db.query(FacturaModel)
        .join(ContratoModel, FacturaModel.contrato_id == ContratoModel.id)
        .filter(ContratoModel.cliente_id == cliente_id)
        .order_by(asc(FacturaModel.id))
        .all()
    )
    out = [
        {
            "id": f.id,
            "nro": f.nro,
            "contrato_id": f.contrato_id,
            "periodo_mes": f.periodo_mes,
            "periodo_anio": f.periodo_anio,
            "subtotal": _float(f.subtotal),
            "mora": _float(f.mora),
            "recargo": _float(f.recargo),
            "total": _float(f.total),
            "estado": f.estado,
            "vencimiento": str(f.vencimiento) if f.vencimiento else None,
        }
        for f in rows
    ]
    return JSONResponse(status_code=200, content=out)


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
        if f.estado == EstadoFacturaEnum.pagada:
            return JSONResponse(
                status_code=422,
                content={"message": "No se puede emitir una factura ya pagada"},
            )
        total = float((f.subtotal or 0) + (f.mora or 0) + (f.recargo or 0))
        if total <= 0:
            return JSONResponse(
                status_code=422,
                content={"message": "Total debe ser mayor a 0 para emitir"},
            )
        f.estado = EstadoFacturaEnum.emitida
        f.emitida_en = datetime.utcnow()
        f.vencimiento = f.periodo_fin + timedelta(days=body.dias_vencimiento)
        f.total = total
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


# =========================================================
# PDF: generar y descargar
# =========================================================
@Factura.post("/facturas/{factura_id}/pdf")
def generar_pdf(factura_id: int, req: Request, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    try:
        if not REPORTLAB_OK:
            return JSONResponse(
                status_code=500,
                content={"message": "Falta dependencia: pip install reportlab"},
            )
        f = db.get(FacturaModel, factura_id)
        if not f:
            return JSONResponse(
                status_code=404, content={"message": "Factura no encontrada"}
            )
        c = db.get(ContratoModel, f.contrato_id)
        if not c:
            return JSONResponse(
                status_code=404, content={"message": "Contrato no encontrado"}
            )
        cli = db.get(ClienteModel, c.cliente_id)
        p = db.get(PlanModel, c.plan_id)
        if not cli or not p:
            return JSONResponse(
                status_code=404,
                content={"message": "Datos incompletos para renderizar"},
            )

        pdf_path = _pdf_path_for(f)
        _render_factura_pdf(pdf_path, f, c, cli, p)

        f.pdf_path = str(pdf_path.relative_to(_storage_root()))
        db.commit()
        db.refresh(f)

        return JSONResponse(
            status_code=200, content={"message": "PDF generado", "pdf_path": f.pdf_path}
        )
    except Exception as ex:
        db.rollback()
        print("Error generar_pdf ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al generar PDF"}
        )


@Factura.get("/facturas/{factura_id}/pdf")
def descargar_pdf(factura_id: int, req: Request, db: Session = Depends(get_db)):
    # Cliente dueño puede descargar su propia factura; admin ve todas
    guard, cliente_id = require_owner_or_roles(
        req.headers, db, allowed_roles={"gerente", "operador"}
    )
    if guard:
        return guard
    try:
        f = db.get(FacturaModel, factura_id)
        if not f:
            return JSONResponse(
                status_code=404, content={"message": "Factura no encontrada"}
            )

        # Ownership si es cliente
        if cliente_id is not None:
            c = db.get(ContratoModel, f.contrato_id)
            if not c or c.cliente_id != cliente_id:
                return JSONResponse(
                    status_code=404, content={"message": "Factura no encontrada"}
                )

        # Path del archivo
        file_path = None
        if f.pdf_path:
            file_path = _storage_root() / f.pdf_path
        else:
            # Intentar localizar por convención
            candidate = _pdf_path_for(f)
            if candidate.exists():
                file_path = candidate

        if not file_path or not Path(file_path).exists():
            return JSONResponse(
                status_code=404, content={"message": "PDF no generado aún"}
            )

        return FileResponse(
            path=str(file_path),
            media_type="application/pdf",
            filename=f"factura_{f.id:06d}.pdf",
        )
    except Exception as ex:
        print("Error descargar_pdf ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al descargar PDF"}
        )
