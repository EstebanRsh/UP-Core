# backend/routes/facturacion.py
from typing import Optional
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from configs.db import get_db
from auth.roles import require_roles
from models.modelo import ConfigFacturacion as ConfigModel

Facturacion = APIRouter(tags=["Configuración"])


class InputConfig(BaseModel):
    company_name: Optional[str] = Field(default=None, max_length=120)
    company_dni: Optional[str] = Field(default=None, max_length=32)
    company_address: Optional[str] = Field(default=None, max_length=200)
    company_contact: Optional[str] = Field(default=None, max_length=200)
    logo_path: Optional[str] = Field(default=None, max_length=200)


@Facturacion.get(
    "/config/facturacion",
    summary="Obtener configuración de facturación",
    description="Devuelve los datos de la empresa para el recibo PDF. Requiere rol gerente u operador.",
)
def get_config(req: Request, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard
    cfg = db.query(ConfigModel).first()
    if not cfg:
        return JSONResponse(
            status_code=200,
            content={
                "company_name": "UP-Core ISP",
                "company_address": "Av. Principal 123, Buenos Aires",
                "company_dni": "30-99999999-7",
                "company_contact": "soporte@upcore.local | +54 11 5555-5555",
                "logo_path": None,
            },
        )
    return JSONResponse(
        status_code=200,
        content={
            "company_name": cfg.company_name,
            "company_dni": cfg.company_dni,
            "company_address": cfg.company_address,
            "company_contact": cfg.company_contact,
            "logo_path": cfg.logo_path,
        },
    )


@Facturacion.put(
    "/config/facturacion",
    summary="Actualizar configuración de facturación",
    description="Actualiza datos de la empresa (nombre, CUIT, dirección, contacto y logo). Requiere rol gerente.",
)
def update_config(body: InputConfig, req: Request, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente"})
    if guard:
        return guard
    try:
        cfg = db.query(ConfigModel).first()
        if not cfg:
            cfg = ConfigModel()
            db.add(cfg)

        if body.company_name is not None:
            cfg.company_name = body.company_name
        if body.company_dni is not None:
            cfg.company_dni = body.company_dni
        if body.company_address is not None:
            cfg.company_address = body.company_address
        if body.company_contact is not None:
            cfg.company_contact = body.company_contact
        if body.logo_path is not None:
            cfg.logo_path = body.logo_path

        db.commit()
        return JSONResponse(
            status_code=200, content={"message": "Configuración actualizada"}
        )
    except Exception as ex:
        db.rollback()
        print("Error update_config ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al actualizar configuración"}
        )
