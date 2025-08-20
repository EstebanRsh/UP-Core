from typing import Optional, Set, Tuple
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .security import Security
from models.modelo import Cliente as ClienteModel


def require_roles(headers, allowed: set[str] | None = None):
    """
    Valida JWT y (opcional) restringe por rol.
    Uso:
        guard = require_roles(req.headers, {"gerente","operador"})
        if guard: return guard
    """
    payload = Security.verify_token(headers)
    if not isinstance(payload, dict) or "iat" not in payload:
        return JSONResponse(status_code=401, content=payload)

    if allowed:
        role = str(payload.get("role") or "").lower()
        if role not in {r.lower() for r in allowed}:
            return JSONResponse(
                status_code=403, content={"message": f"Prohibido para rol '{role}'"}
            )
    return None


def require_owner_or_roles(
    headers,
    db: Session,
    allowed_roles: Optional[Set[str]] = None,
    not_found_on_forbidden: bool = True,
) -> Tuple[Optional[JSONResponse], Optional[int]]:
    """
    Devuelve (guard, cliente_id). Si guard != None, devolvelo.
    Si el rol está en allowed_roles => acceso total (cliente_id=None).
    Si es 'cliente' => retorna su cliente_id para filtrar por pertenencia.
    Si no cumple => 403/404 según política.
    """
    payload = Security.verify_token(headers)
    if not isinstance(payload, dict) or "iat" not in payload:
        return JSONResponse(status_code=401, content=payload), None

    role = str(payload.get("role") or "").lower()

    # Roles privilegiados (gerente/operador u otros que autorices)
    if allowed_roles and role in {r.lower() for r in allowed_roles}:
        return None, None

    # Cliente dueño
    if role == "cliente":
        user_id = payload.get("user_id")
        if not user_id:
            return (
                JSONResponse(status_code=401, content={"message": "Token sin user_id"}),
                None,
            )
        cli = db.query(ClienteModel).filter(ClienteModel.usuario_id == user_id).first()
        if not cli:
            return (
                JSONResponse(
                    status_code=404,
                    content={"message": "Cliente no vinculado a este usuario"},
                ),
                None,
            )
        return None, cli.id

    # Otros roles no permitidos
    if allowed_roles:
        if not_found_on_forbidden:
            return (
                JSONResponse(
                    status_code=404, content={"message": "Recurso no encontrado"}
                ),
                None,
            )
        else:
            return (
                JSONResponse(
                    status_code=403, content={"message": f"Prohibido para rol '{role}'"}
                ),
                None,
            )

    return JSONResponse(status_code=403, content={"message": "Solo clientes"}), None
