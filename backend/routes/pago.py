# backend/routes/pago.py
from datetime import datetime
from typing import Optional, List
import os, uuid, shutil, re, unicodedata
from pathlib import Path

from fastapi import APIRouter, Request, Depends, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

from sqlalchemy.orm import Session
from sqlalchemy import asc, func

from configs.db import get_db
from auth.roles import require_roles, require_owner_or_roles
from models.modelo import (
    Pago as PagoModel,
    Factura as FacturaModel,
    Contrato as ContratoModel,
    Cliente as ClienteModel,
    ConfigFacturacion as ConfigFacturacionModel,
    EstadoPagoEnum,
    MetodoPagoEnum,
    EstadoFacturaEnum,
)

# HTML→PDF
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    from weasyprint import HTML, CSS

    WEASY_OK = True
except Exception:
    WEASY_OK = False

Pago = APIRouter(tags=["Pagos"])


# ===============================
# Schemas
# ===============================
class InputPagoCreate(BaseModel):
    factura_id: int
    monto: float = Field(gt=0)
    metodo: MetodoPagoEnum
    referencia: Optional[str] = None
    comprobante_path: Optional[str] = None
    confirmar: bool = True
    generar_recibo: bool = True  # autogenerar recibo al crear


class InputPaginatedRequest(BaseModel):
    limit: int = Field(default=25, ge=1, le=100)
    last_seen_id: Optional[int] = None


# ===============================
# Helpers
# ===============================
def _float(n):
    return float(n) if n is not None else None


def _storage_root() -> Path:
    return Path(__file__).resolve().parent.parent / "storage"


def _assets_root() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "pdf"


def _comprobante_dir() -> Path:
    base = _storage_root() / "comprobantes"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _slugify(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    s = "".join([c for c in nfkd if not unicodedata.combining(c)])
    s = s.lower().replace(" ", "_")
    s = re.sub(r"[^a-z0-9_-]", "", s)
    s = re.sub(r"_{2,}", "_", s)
    return s.strip("_")


def _recibo_dir(pago: PagoModel) -> Path:
    # /storage/recibos/AAAA/MM/DD/
    dt = pago.fecha or datetime.utcnow()
    base = (
        _storage_root() / "recibos" / f"{dt.year}" / f"{dt.month:02d}" / f"{dt.day:02d}"
    )
    base.mkdir(parents=True, exist_ok=True)
    return base


def _recibo_filename(
    pago: PagoModel, factura: FacturaModel, cliente: ClienteModel
) -> str:
    # rec_{DDMMAAAA}_{apellido}_{nombre}_per-{MMAAAA}_p{pagoId}.pdf
    dt = pago.fecha or datetime.utcnow()
    ddmmyyyy = dt.strftime("%d%m%Y")
    per_mmaaaa = f"{factura.periodo_mes:02d}{factura.periodo_anio}"
    apellido = _slugify(cliente.apellido or "")
    nombre = _slugify(cliente.nombre or "")
    return f"rec_{ddmmyyyy}_{apellido}_{nombre}_per-{per_mmaaaa}_p{pago.id}.pdf"


def _recibo_path_for(
    pago: PagoModel, factura: FacturaModel, cliente: ClienteModel
) -> Path:
    return _recibo_dir(pago) / _recibo_filename(pago, factura, cliente)


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


def _get_company_config(db: Session) -> dict:
    cfg = db.query(ConfigFacturacionModel).first()
    if cfg:
        return {
            "company_name": cfg.company_name,
            "company_address": cfg.company_address,
            "company_dni": cfg.company_dni,
            "company_contact": cfg.company_contact,
            "logo_path": cfg.logo_path,
        }
    return {
        "company_name": "UP-Core ISP",
        "company_address": "Av. Principal 123, Buenos Aires",
        "company_dni": "30-99999999-7",
        "company_contact": "soporte@upcore.local | +54 11 5555-5555",
        "logo_path": None,
    }


# ===============================
# PDF Recibo (HTML/CSS)
# ===============================
def _render_recibo_weasy(
    destino: Path,
    pago: PagoModel,
    factura: FacturaModel,
    contrato: ContratoModel,
    cliente: ClienteModel,
    company: dict,
):
    if not WEASY_OK:
        raise RuntimeError("Faltan dependencias: weasyprint/jinja2/tinycss2/cssselect2")

    env = Environment(
        loader=FileSystemLoader(str(_assets_root())),
        autoescape=select_autoescape(["html", "xml"]),
    )
    tpl = env.get_template("receipt.html")

    data = {
        "receipt": {
            "logo_path": company["logo_path"],
            "company_name": company["company_name"],
            "company_address": company["company_address"],
            "company_dni": company["company_dni"],
            "company_contact": company["company_contact"],
            "client_name": f"{cliente.apellido}, {cliente.nombre}",
            "client_dni": f"Doc: {cliente.documento}",
            "client_address": cliente.direccion or "",
            "client_phone": cliente.telefono or "",
            "client_email": cliente.email or "",
            "receipt_number": f"REC-{pago.id:06d}",
            "payment_date": (pago.fecha or datetime.utcnow()).strftime("%Y-%m-%d"),
            "item_description": f"Pago de factura {factura.nro} - Servicio {contrato.id}",
            "base_amount": float(pago.monto or 0),
            "late_fee": float(factura.mora or 0),
            "total_paid": float(pago.monto or 0),
            "payment_method": pago.metodo,
            "invoice_number": factura.nro
            or f"{factura.periodo_anio}{factura.periodo_mes:02d}-{factura.id:06d}",
            "due_date": factura.vencimiento.isoformat() if factura.vencimiento else "-",
        }
    }

    css = _assets_root() / "style.css"
    HTML(string=tpl.render(**data), base_url=str(_assets_root())).write_pdf(
        target=str(destino), stylesheets=[CSS(filename=str(css))]
    )


# ===============================
# Rutas
# ===============================
@Pago.get(
    "/pagos/hello",
    summary="Probar módulo Pagos",
    description="Endpoint de prueba para verificar que el router de pagos responde.",
)
def hello_pagos():
    return "Hello Pagos!!!"


@Pago.post(
    "/pagos",
    summary="Registrar pago",
    description="Crea un pago, recalcula estado de la factura y opcionalmente genera el recibo PDF.",
)
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

        if body.generar_recibo and WEASY_OK:
            c = db.get(ContratoModel, f.contrato_id)
            cli = db.get(ClienteModel, c.cliente_id) if c else None
            if c and cli:
                destino = _recibo_path_for(nuevo, f, cli)
                company = _get_company_config(db)
                _render_recibo_weasy(destino, nuevo, f, c, cli, company)
                nuevo.recibo_path = str(destino.relative_to(_storage_root()))
                db.commit()
                db.refresh(nuevo)

        return JSONResponse(
            status_code=201,
            content={
                "id": nuevo.id,
                "factura_id": nuevo.factura_id,
                "monto": _float(nuevo.monto),
                "metodo": nuevo.metodo,
                "estado": nuevo.estado,
                "factura_estado": f.estado,
                "recibo_path": nuevo.recibo_path,
            },
        )
    except Exception as ex:
        db.rollback()
        print("Error crear_pago ---->> ", ex)
        return JSONResponse(status_code=500, content={"message": "Error al crear pago"})


@Pago.get(
    "/pagos/factura/{factura_id}",
    summary="Listar pagos de una factura (admin)",
    description="Devuelve los pagos asociados a una factura. Requiere rol gerente u operador.",
)
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
                "recibo_path": p.recibo_path,
            }
            for p in rows
        ]
        return JSONResponse(status_code=200, content=out)
    except Exception as ex:
        print("Error pagos_por_factura ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al listar pagos"}
        )


@Pago.get(
    "/pagos/all",
    summary="Listar todos los pagos (admin)",
    description="Lista completa de pagos para administración. Requiere rol gerente u operador.",
)
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
                "recibo_path": p.recibo_path,
            }
            for p in rows
        ]
        return JSONResponse(status_code=200, content=out)
    except Exception as ex:
        print("Error listar_pagos ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al listar pagos"}
        )


@Pago.post(
    "/pagos/paginated",
    summary="Listar pagos paginados (admin)",
    description="Devuelve pagos paginados por id ascendente. Requiere rol gerente u operador.",
)
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
                "recibo_path": p.recibo_path,
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


# ===============================
# Upload / download comprobante
# ===============================
ALLOWED_MIMES = {"application/pdf", "image/jpeg", "image/png"}
ALLOWED_EXTS = {"pdf", "jpg", "jpeg", "png"}


@Pago.post(
    "/pagos/{pago_id}/comprobante",
    summary="Subir comprobante de pago",
    description="Adjunta un comprobante (PDF/JPG/PNG). Disponible para gerente/operador y cliente dueño.",
)
async def subir_comprobante(
    pago_id: int,
    req: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    guard, cliente_id = require_owner_or_roles(
        req.headers, db, allowed_roles={"gerente", "operador"}
    )
    if guard:
        return guard
    try:
        p = db.get(PagoModel, pago_id)
        if not p:
            return JSONResponse(
                status_code=404, content={"message": "Pago no encontrado"}
            )
        f = db.get(FacturaModel, p.factura_id)
        c = db.get(ContratoModel, f.contrato_id) if f else None
        if not f or not c:
            return JSONResponse(
                status_code=404, content={"message": "Factura/Contrato no encontrado"}
            )

        if cliente_id is not None and c.cliente_id != cliente_id:
            return JSONResponse(
                status_code=404, content={"message": "Pago no encontrado"}
            )

        content_type = (file.content_type or "").lower()
        ext = (os.path.splitext(file.filename or "")[1][1:] or "").lower()
        if content_type not in ALLOWED_MIMES or ext not in ALLOWED_EXTS:
            return JSONResponse(
                status_code=415,
                content={"message": "Formato no permitido. Use PDF/JPG/PNG"},
            )

        destino_dir = (
            _comprobante_dir()
            / f"{datetime.utcnow().year}"
            / f"{datetime.utcnow().month:02d}"
        )
        destino_dir.mkdir(parents=True, exist_ok=True)
        nombre = f"pago_{pago_id}_{uuid.uuid4().hex[:8]}.{ext}"
        destino = destino_dir / nombre

        with destino.open("wb") as out:
            shutil.copyfileobj(file.file, out)

        p.comprobante_path = str(destino.relative_to(_storage_root()))
        db.commit()
        db.refresh(p)

        return JSONResponse(
            status_code=200,
            content={
                "message": "Comprobante subido",
                "comprobante_path": p.comprobante_path,
            },
        )
    except Exception as ex:
        db.rollback()
        print("Error subir_comprobante ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al subir comprobante"}
        )


@Pago.get(
    "/pagos/{pago_id}/comprobante",
    summary="Descargar comprobante de pago",
    description="Devuelve el comprobante si existe y el usuario tiene permiso.",
)
def descargar_comprobante(pago_id: int, req: Request, db: Session = Depends(get_db)):
    guard, cliente_id = require_owner_or_roles(
        req.headers, db, allowed_roles={"gerente", "operador"}
    )
    if guard:
        return guard
    try:
        p = db.get(PagoModel, pago_id)
        if not p:
            return JSONResponse(
                status_code=404, content={"message": "Pago no encontrado"}
            )
        f = db.get(FacturaModel, p.factura_id)
        c = db.get(ContratoModel, f.contrato_id) if f else None
        if not f or not c:
            return JSONResponse(
                status_code=404, content={"message": "Factura/Contrato no encontrado"}
            )

        if cliente_id is not None and c.cliente_id != cliente_id:
            return JSONResponse(
                status_code=404, content={"message": "Comprobante no encontrado"}
            )

        if not p.comprobante_path:
            return JSONResponse(
                status_code=404, content={"message": "Comprobante no disponible"}
            )
        file_path = _storage_root() / p.comprobante_path
        if not file_path.exists():
            return JSONResponse(
                status_code=404,
                content={"message": "Archivo no encontrado en servidor"},
            )

        ext = file_path.suffix.lower()
        mime = "application/octet-stream"
        if ext == ".pdf":
            mime = "application/pdf"
        elif ext in (".jpg", ".jpeg"):
            mime = "image/jpeg"
        elif ext == ".png":
            mime = "image/png"

        return FileResponse(
            path=str(file_path), media_type=mime, filename=file_path.name
        )
    except Exception as ex:
        print("Error descargar_comprobante ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al descargar comprobante"}
        )


# ===============================
# Recibo PDF: generar y descargar
# ===============================
@Pago.post(
    "/pagos/{pago_id}/recibo",
    summary="Generar recibo PDF",
    description="Genera el PDF del recibo con la plantilla HTML/CSS y persiste el path en BD.",
)
def generar_recibo(pago_id: int, req: Request, db: Session = Depends(get_db)):
    guard, cliente_id = require_owner_or_roles(
        req.headers, db, allowed_roles={"gerente", "operador"}
    )
    if guard:
        return guard
    try:
        if not WEASY_OK:
            return JSONResponse(
                status_code=500,
                content={
                    "message": "Faltan dependencias: conda install -c conda-forge weasyprint jinja2 tinycss2 cssselect2"
                },
            )

        p = db.get(PagoModel, pago_id)
        if not p:
            return JSONResponse(
                status_code=404, content={"message": "Pago no encontrado"}
            )
        f = db.get(FacturaModel, p.factura_id)
        c = db.get(ContratoModel, f.contrato_id) if f else None
        cli = db.get(ClienteModel, c.cliente_id) if c else None
        if not f or not c or not cli:
            return JSONResponse(
                status_code=404, content={"message": "Datos incompletos"}
            )

        if cliente_id is not None and c.cliente_id != cliente_id:
            return JSONResponse(
                status_code=404, content={"message": "Pago no encontrado"}
            )

        destino = _recibo_path_for(p, f, cli)
        company = _get_company_config(db)
        _render_recibo_weasy(destino, p, f, c, cli, company)

        p.recibo_path = str(destino.relative_to(_storage_root()))
        db.commit()
        db.refresh(p)

        return JSONResponse(
            status_code=200,
            content={
                "message": "Recibo generado",
                "recibo_path": p.recibo_path,
            },
        )
    except Exception as ex:
        print("Error generar_recibo ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al generar recibo"}
        )


@Pago.get(
    "/pagos/{pago_id}/recibo",
    summary="Descargar recibo PDF",
    description="Descarga el PDF del recibo si existe y el usuario tiene permiso.",
)
def descargar_recibo(pago_id: int, req: Request, db: Session = Depends(get_db)):
    guard, cliente_id = require_owner_or_roles(
        req.headers, db, allowed_roles={"gerente", "operador"}
    )
    if guard:
        return guard
    try:
        p = db.get(PagoModel, pago_id)
        if not p:
            return JSONResponse(
                status_code=404, content={"message": "Pago no encontrado"}
            )
        f = db.get(FacturaModel, p.factura_id)
        c = db.get(ContratoModel, f.contrato_id) if f else None
        cli = db.get(ClienteModel, c.cliente_id) if c else None
        if not f or not c or not cli:
            return JSONResponse(
                status_code=404, content={"message": "Datos incompletos"}
            )

        if cliente_id is not None and c.cliente_id != cliente_id:
            return JSONResponse(
                status_code=404, content={"message": "Recibo no encontrado"}
            )

        if p.recibo_path:
            file_path = _storage_root() / p.recibo_path
        else:
            file_path = _recibo_path_for(p, f, cli)

        if not file_path.exists():
            return JSONResponse(
                status_code=404, content={"message": "Recibo no generado aún"}
            )

        return FileResponse(
            path=str(file_path), media_type="application/pdf", filename=file_path.name
        )
    except Exception as ex:
        print("Error descargar_recibo ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al descargar recibo"}
        )
