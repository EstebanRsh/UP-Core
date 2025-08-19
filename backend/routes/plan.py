# backend/routes/plan.py
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import asc

from configs.db import get_db
from models.modelo import Plan as PlanModel
from auth.security import Security

Plan = APIRouter()


# ---------- Schemas ----------
class InputPlanCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    vel_down: int = Field(gt=0)  # Mbps
    vel_up: int = Field(gt=0)  # Mbps
    precio_mensual: float = Field(gt=0)  # ARS
    descripcion: Optional[str] = None
    activo: bool = True


class InputPlanUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=2, max_length=120)
    vel_down: Optional[int] = Field(default=None, gt=0)
    vel_up: Optional[int] = Field(default=None, gt=0)
    precio_mensual: Optional[float] = Field(default=None, gt=0)
    descripcion: Optional[str] = None
    activo: Optional[bool] = None


class InputPaginatedRequest(BaseModel):
    limit: int = Field(default=25, ge=1, le=100)
    last_seen_id: Optional[int] = None


# ---------- Helpers ----------
def _require_token(req: Request):
    payload = Security.verify_token(req.headers)
    if "iat" not in payload:
        return payload, False
    return payload, True


# ---------- Rutas ----------
@Plan.get("/planes/hello")
def hello_planes():
    return "Hello Planes!!!"


@Plan.post("/planes")
def crear_plan(req: Request, body: InputPlanCreate, db: Session = Depends(get_db)):
    try:
        _, ok = _require_token(req)
        if not ok:
            return JSONResponse(status_code=401, content={"message": "No autorizado"})

        # unicidad por nombre
        exists = db.query(PlanModel).filter(PlanModel.nombre == body.nombre).first()
        if exists:
            return JSONResponse(
                status_code=409, content={"message": "Ya existe un plan con ese nombre"}
            )

        nuevo = PlanModel(
            nombre=body.nombre,
            vel_down=body.vel_down,
            vel_up=body.vel_up,
            precio_mensual=body.precio_mensual,
            descripcion=body.descripcion,
            activo=body.activo,
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)

        return JSONResponse(
            status_code=201,
            content={
                "id": nuevo.id,
                "nombre": nuevo.nombre,
                "vel_down": nuevo.vel_down,
                "vel_up": nuevo.vel_up,
                "precio_mensual": float(nuevo.precio_mensual),
                "descripcion": nuevo.descripcion,
                "activo": nuevo.activo,
            },
        )
    except Exception as ex:
        db.rollback()
        print("Error crear_plan ---->> ", ex)
        return JSONResponse(status_code=500, content={"message": "Error al crear plan"})


@Plan.get("/planes/all")
def listar_planes(req: Request, db: Session = Depends(get_db)):
    try:
        _, ok = _require_token(req)
        if not ok:
            return JSONResponse(status_code=401, content={"message": "No autorizado"})

        rows: List[PlanModel] = db.query(PlanModel).order_by(asc(PlanModel.id)).all()
        salida = [
            {
                "id": p.id,
                "nombre": p.nombre,
                "vel_down": p.vel_down,
                "vel_up": p.vel_up,
                "precio_mensual": float(p.precio_mensual),
                "descripcion": p.descripcion,
                "activo": p.activo,
            }
            for p in rows
        ]
        return JSONResponse(status_code=200, content=salida)
    except Exception as ex:
        print("Error listar_planes ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al listar planes"}
        )


@Plan.post("/planes/paginated")
def planes_paginados(
    req: Request, body: InputPaginatedRequest, db: Session = Depends(get_db)
):
    try:
        _, ok = _require_token(req)
        if not ok:
            return JSONResponse(status_code=401, content={"message": "No autorizado"})

        q = db.query(PlanModel).order_by(asc(PlanModel.id))
        if body.last_seen_id is not None:
            q = q.filter(PlanModel.id > body.last_seen_id)
        rows = q.limit(body.limit).all()

        salida = [
            {
                "id": p.id,
                "nombre": p.nombre,
                "vel_down": p.vel_down,
                "vel_up": p.vel_up,
                "precio_mensual": float(p.precio_mensual),
                "descripcion": p.descripcion,
                "activo": p.activo,
            }
            for p in rows
        ]
        next_cursor = salida[-1]["id"] if len(salida) == body.limit else None
        return JSONResponse(
            status_code=200, content={"planes": salida, "next_cursor": next_cursor}
        )
    except Exception as ex:
        print("Error planes_paginados ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al paginar planes"}
        )


@Plan.get("/planes/{plan_id}")
def obtener_plan(plan_id: int, req: Request, db: Session = Depends(get_db)):
    try:
        _, ok = _require_token(req)
        if not ok:
            return JSONResponse(status_code=401, content={"message": "No autorizado"})

        p = db.get(PlanModel, plan_id)
        if not p:
            return JSONResponse(
                status_code=404, content={"message": "Plan no encontrado"}
            )
        return JSONResponse(
            status_code=200,
            content={
                "id": p.id,
                "nombre": p.nombre,
                "vel_down": p.vel_down,
                "vel_up": p.vel_up,
                "precio_mensual": float(p.precio_mensual),
                "descripcion": p.descripcion,
                "activo": p.activo,
            },
        )
    except Exception as ex:
        print("Error obtener_plan ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al obtener plan"}
        )


@Plan.put("/planes/{plan_id}")
def actualizar_plan(
    plan_id: int, body: InputPlanUpdate, req: Request, db: Session = Depends(get_db)
):
    try:
        _, ok = _require_token(req)
        if not ok:
            return JSONResponse(status_code=401, content={"message": "No autorizado"})

        p = db.get(PlanModel, plan_id)
        if not p:
            return JSONResponse(
                status_code=404, content={"message": "Plan no encontrado"}
            )

        if body.nombre and body.nombre != p.nombre:
            exists = db.query(PlanModel).filter(PlanModel.nombre == body.nombre).first()
            if exists:
                return JSONResponse(
                    status_code=409,
                    content={"message": "Ya existe un plan con ese nombre"},
                )
            p.nombre = body.nombre

        if body.vel_down is not None:
            p.vel_down = body.vel_down
        if body.vel_up is not None:
            p.vel_up = body.vel_up
        if body.precio_mensual is not None:
            p.precio_mensual = body.precio_mensual
        if body.descripcion is not None:
            p.descripcion = body.descripcion
        if body.activo is not None:
            p.activo = body.activo

        db.commit()
        db.refresh(p)
        return JSONResponse(status_code=200, content={"message": "Plan actualizado"})
    except Exception as ex:
        db.rollback()
        print("Error actualizar_plan ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al actualizar plan"}
        )


@Plan.delete("/planes/{plan_id}")
def desactivar_plan(plan_id: int, req: Request, db: Session = Depends(get_db)):
    try:
        _, ok = _require_token(req)
        if not ok:
            return JSONResponse(status_code=401, content={"message": "No autorizado"})

        p = db.get(PlanModel, plan_id)
        if not p:
            return JSONResponse(
                status_code=404, content={"message": "Plan no encontrado"}
            )

        p.activo = False
        db.commit()
        return JSONResponse(status_code=200, content={"message": "Plan desactivado"})
    except Exception as ex:
        db.rollback()
        print("Error desactivar_plan ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al desactivar plan"}
        )
