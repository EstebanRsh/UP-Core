# backend/routes/usuario.py
from typing import Optional
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from configs.db import get_db
from models.modelo import Usuario as UsuarioModel, RoleEnum, Cliente as ClienteModel
from auth.security import Security
from auth.roles import require_roles

Usuario = APIRouter(tags=["Usuarios"])


# --------- Schemas ---------
class InputUsuarioCreate(BaseModel):
    email: Optional[EmailStr] = None
    documento: Optional[str] = Field(default=None, max_length=11)
    password: str = Field(min_length=4)
    role: RoleEnum = RoleEnum.operador


class InputLogin(BaseModel):
    email: Optional[EmailStr] = None
    documento: Optional[str] = Field(default=None, max_length=11)
    password: str


class InputPaginatedRequest(BaseModel):
    limit: int = Field(default=25, ge=1, le=100)
    last_seen_id: Optional[int] = None


# --------- Rutas ---------
@Usuario.get(
    "/",
    summary="Probar módulo Usuarios",
    description="Endpoint de prueba para verificar que el router de usuarios responde.",
)
def hello_user():
    return "Hello User!!!"


@Usuario.get(
    "/me",
    summary="Perfil del usuario autenticado",
    description="Devuelve información básica del usuario autenticado, incluyendo role y cliente_id si aplica.",
)
def me(req: Request, db: Session = Depends(get_db)):
    payload = Security.verify_token(req.headers)
    if not isinstance(payload, dict) or "iat" not in payload:
        return JSONResponse(status_code=401, content=payload)

    role = payload.get("role")
    user_id = payload.get("user_id")
    cliente_id = None

    if role == "cliente" and user_id:
        cli = db.query(ClienteModel).filter(ClienteModel.usuario_id == user_id).first()
        cliente_id = cli.id if cli else None

    return JSONResponse(
        status_code=200,
        content={
            "user_id": user_id,
            "username": payload.get("username"),
            "role": role,
            "cliente_id": cliente_id,
        },
    )


@Usuario.get(
    "/users/all",
    summary="Listar usuarios (admin)",
    description="Devuelve todos los usuarios con datos básicos. Requiere rol gerente u operador.",
)
def get_all_users(req: Request, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard

    rows = db.query(UsuarioModel).order_by(UsuarioModel.id.asc()).all()
    return JSONResponse(
        status_code=200,
        content=[
            {
                "id": u.id,
                "email": u.email,
                "documento": u.documento,
                "role": u.role,
                "activo": u.activo,
                "creado_en": u.creado_en.isoformat() if u.creado_en else None,
            }
            for u in rows
        ],
    )


@Usuario.post(
    "/users/paginated",
    summary="Listar usuarios paginados (admin)",
    description="Lista usuarios usando cursor por id. Requiere rol gerente u operador.",
)
def get_users_paginated(
    req: Request, body: InputPaginatedRequest, db: Session = Depends(get_db)
):
    guard = require_roles(req.headers, {"gerente", "operador"})
    if guard:
        return guard

    q = db.query(UsuarioModel).order_by(UsuarioModel.id.asc())
    if body.last_seen_id is not None:
        q = q.filter(UsuarioModel.id > body.last_seen_id)
    rows = q.limit(body.limit).all()
    salida = [
        {
            "id": u.id,
            "email": u.email,
            "documento": u.documento,
            "role": u.role,
            "activo": u.activo,
            "creado_en": u.creado_en.isoformat() if u.creado_en else None,
        }
        for u in rows
    ]
    next_cursor = salida[-1]["id"] if len(salida) == body.limit else None
    return JSONResponse(
        status_code=200, content={"users": salida, "next_cursor": next_cursor}
    )


@Usuario.post(
    "/users/login",
    summary="Iniciar sesión y obtener JWT",
    description="Permite autenticarse con documento o email. Devuelve token JWT y rol.",
)
def login_user(us: InputLogin, db: Session = Depends(get_db)):
    try:
        if not us.email and not us.documento:
            return JSONResponse(
                status_code=422, content={"message": "Debe enviar email o documento"}
            )

        if us.email:
            user = (
                db.query(UsuarioModel)
                .filter(UsuarioModel.email == us.email.lower())
                .first()
            )
        else:
            doc_norm = "".join(c for c in (us.documento or "") if c.isdigit())
            user = (
                db.query(UsuarioModel)
                .filter(UsuarioModel.documento == doc_norm)
                .first()
            )

        if not user:
            return JSONResponse(
                status_code=404, content={"message": "Usuario no encontrado"}
            )

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


@Usuario.post(
    "/users/add",
    summary="Crear usuario (solo gerente)",
    description="Crea un usuario administrativo o cliente. Requiere rol gerente.",
)
def create_user(us: InputUsuarioCreate, req: Request, db: Session = Depends(get_db)):
    guard = require_roles(req.headers, {"gerente"})
    if guard:
        return guard
    try:
        if not us.email and not us.documento:
            return JSONResponse(
                status_code=422, content={"message": "Debe enviar email o documento"}
            )

        doc_norm = "".join(c for c in (us.documento or "") if c.isdigit()) or None

        if (
            us.email
            and db.query(UsuarioModel)
            .filter(UsuarioModel.email == us.email.lower())
            .first()
        ):
            return JSONResponse(
                status_code=409, content={"message": "Email ya registrado"}
            )
        if (
            doc_norm
            and db.query(UsuarioModel)
            .filter(UsuarioModel.documento == doc_norm)
            .first()
        ):
            return JSONResponse(
                status_code=409, content={"message": "Documento ya registrado"}
            )

        nuevo = UsuarioModel(
            email=us.email.lower() if us.email else None,
            documento=doc_norm,
            password_hash=us.password,  # TODO: reemplazar por hash
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
