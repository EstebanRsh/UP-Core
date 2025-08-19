import datetime, pytz, jwt


class Security:
    secret = "cualquier cosa"

    @classmethod
    def hoy(cls):
        return datetime.datetime.now(pytz.timezone("America/Buenos_Aires"))

    @classmethod
    def generate_token(cls, authUser):
        uname = (
            getattr(authUser, "username", None)
            or getattr(authUser, "email", None)
            or getattr(authUser, "documento", None)
        )
        role = getattr(authUser, "role", None)

        try:
            role = role.value if hasattr(role, "value") else role
        except Exception:
            pass
        payload = {
            "iat": cls.hoy(),
            "exp": cls.hoy() + datetime.timedelta(minutes=480),
            "username": uname,
            "role": role,  # 👈 ahora el token lleva el rol
            "user_id": getattr(
                authUser, "id", None
            ),  # 👈 opcional, útil para ownership
        }
        try:
            return jwt.encode(payload, cls.secret, algorithm="HS256")
        except Exception:
            return None

    @classmethod
    def verify_token(cls, headers):
        auth = headers.get("authorization") if hasattr(headers, "get") else None
        if auth:
            try:
                tkn = auth.split(" ")[1]
                payload = jwt.decode(tkn, cls.secret, algorithms=["HS256"])
                return payload
            except jwt.ExpiredSignatureError:
                return {"message": "El token ha expirado!"}
            except jwt.InvalidSignatureError:
                return {"message": "Error de firma invalida!"}
            except jwt.DecodeError:
                return {"message": "Error de decodificación de token!"}
            except Exception:
                return {"message": "Error desconocido durante la validación del token!"}
        else:
            return {"message": "Error, header inexistente!"}
