# backend/auth/roles.py
from fastapi.responses import JSONResponse
from .security import Security


def require_roles(headers, allowed: set[str] | None = None):
    """
    Valida token y, si 'allowed' está definido, exige que payload['role'] esté dentro.
    Devuelve:
      - JSONResponse (401/403) si falla, o
      - None si todo OK.
    Uso:
      guard = require_roles(req.headers, {"gerente","operador"})
      if guard: return guard
    """
    payload = Security.verify_token(headers)
    # token inválido
    if not isinstance(payload, dict) or "iat" not in payload:
        return JSONResponse(status_code=401, content=payload)

    if allowed:
        role = str(payload.get("role") or "").lower()
        if role not in {r.lower() for r in allowed}:
            return JSONResponse(
                status_code=403, content={"message": f"Prohibido para rol '{role}'"}
            )

    return None  # OK
