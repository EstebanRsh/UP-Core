# routes/usuario.py
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field

from sqlalchemy.orm import Session
from sqlalchemy import asc

from configs.db import get_db
from models.modelo import Usuario, RoleEnum
from auth.security import Security  # ajusta a tu ruta real si es necesario

UsuarioRouter = APIRouter()


# --------- Schemas (simples, locales al router) ---------
class InputUsuarioCreate(BaseModel):
    # cualquiera de los dos puede venir; al menos uno requerido
    email: Optional[EmailStr] = None
    documento: Optional[str] = Field(default=None, max_length=11)
    password: str = Field(min_length=4)
    role: RoleEnum = RoleEnum.operador  # por defecto operador


class InputLogin(BaseModel):
    email: Optional[EmailStr] = None
    documento: Optional[str] = Field(default=None, max_length=11)
    password: str


class InputPaginatedRequest(BaseModel):
    limit: int = Field(default=25, ge=1, le=100)
    last_seen_id: Optional[int] = None


# --------- Rutas ---------
@UsuarioRouter.get("/")
def hello_user():
    return "Hello User!!!"


@UsuarioRouter.get("/users/all")
def get_all_users(req: Request, db: Session = Depends(get_db)):
    try:
        has_access = Security.verify_token(req.headers)
        if "iat" not in has_access:
            return JSONResponse(status_code=401, content=has_access)

        users: List[Usuario] = db.query(Usuario).order_by(asc(Usuario.id)).all()
        salida = []
        for u in users:
            salida.append(
                {
                    "id": u.id,
                    "email": u.email,
                    "documento": u.documento,
                    "role": u.role,
                    "activo": u.activo,
                    "creado_en": (
                        u.creado_en.isoformat()
                        if isinstance(u.creado_en, datetime)
                        else str(u.creado_en)
                    ),
                }
            )
        return JSONResponse(status_code=200, content=salida)
    except Exception as ex:
        print("Error get_all_users ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al obtener los usuarios"}
        )


@UsuarioRouter.post("/users/paginated")
def get_users_paginated(
    req: Request, body: InputPaginatedRequest, db: Session = Depends(get_db)
):
    try:
        has_access = Security.verify_token(req.headers)
        if "iat" not in has_access:
            return JSONResponse(status_code=401, content=has_access)

        q = db.query(Usuario).order_by(asc(Usuario.id))
        if body.last_seen_id is not None:
            q = q.filter(Usuario.id > body.last_seen_id)

        rows = q.limit(body.limit).all()
        salida = [
            {
                "id": u.id,
                "email": u.email,
                "documento": u.documento,
                "role": u.role,
                "activo": u.activo,
                "creado_en": (
                    u.creado_en.isoformat()
                    if isinstance(u.creado_en, datetime)
                    else str(u.creado_en)
                ),
            }
            for u in rows
        ]

        next_cursor = salida[-1]["id"] if len(salida) == body.limit else None
        return JSONResponse(
            status_code=200, content={"users": salida, "next_cursor": next_cursor}
        )
    except Exception as ex:
        print("Error get_users_paginated ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al obtener página de usuarios"}
        )


@UsuarioRouter.post("/users/add")
def create_user(us: InputUsuarioCreate, db: Session = Depends(get_db)):
    try:
        if not us.email and not us.documento:
            return JSONResponse(
                status_code=422, content={"message": "Debe enviar email o documento"}
            )

        # normalizo documento a solo dígitos si viene
        doc_norm = "".join(c for c in us.documento or "" if c.isdigit()) or None

        # unicidad simple
        if (
            us.email
            and db.query(Usuario).filter(Usuario.email == us.email.lower()).first()
        ):
            return JSONResponse(
                status_code=409, content={"message": "Email ya registrado"}
            )
        if doc_norm and db.query(Usuario).filter(Usuario.documento == doc_norm).first():
            return JSONResponse(
                status_code=409, content={"message": "Documento ya registrado"}
            )

        nuevo = Usuario(
            email=us.email.lower() if us.email else None,
            documento=doc_norm,
            # por simplicidad guardamos plano en password_hash (luego lo cambiamos por hash)
            password_hash=us.password,
            role=us.role,
            activo=True,
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)

        return JSONResponse(
            status_code=201,
            content={
                "id": nuevo.id,
                "email": nuevo.email,
                "documento": nuevo.documento,
                "role": nuevo.role,
                "activo": nuevo.activo,
            },
        )
    except Exception as ex:
        db.rollback()
        print("Error create_user ---->> ", ex)
        return JSONResponse(
            status_code=500, content={"message": "Error al crear usuario"}
        )


@UsuarioRouter.post("/users/login")
def login_user(us: InputLogin, db: Session = Depends(get_db)):
    try:
        if not us.email and not us.documento:
            return JSONResponse(
                status_code=422, content={"message": "Debe enviar email o documento"}
            )

        user = None
        if us.email:
            user = db.query(Usuario).filter(Usuario.email == us.email.lower()).first()
        else:
            doc_norm = "".join(c for c in (us.documento or "") if c.isdigit())
            user = db.query(Usuario).filter(Usuario.documento == doc_norm).first()

        if not user:
            return JSONResponse(
                status_code=404, content={"message": "Usuario no encontrado"}
            )

        # por ahora comparamos plano contra password_hash (luego implementamos hash)
        if user.password_hash != us.password:
            return JSONResponse(
                status_code=401, content={"message": "Credenciales inválidas"}
            )

        token = Security.generate_token(user)
        if not token:
            return JSONResponse(
                status_code=500, content={"message": "Error al generar token"}
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "token": token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "documento": user.documento,
                    "role": user.role,
                    "activo": user.activo,
                },
                "message": "User logged in successfully!",
            },
        )
    except Exception as ex:
        print("Error login_user ---->> ", ex)
        return JSONResponse(status_code=500, content={"message": "Error en login"})
