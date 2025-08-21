# UP-Core — ISP Manager (Backend FastAPI)

## Resumen

UP-Core es un backend para la gestión de un ISP: usuarios (roles), clientes, planes,
contratos, facturas administrativas y pagos (con **recibo PDF**). Está diseñado para
ser simple, entendible por un perfil junior y fácil de mantener/expandir.

- Framework: FastAPI
- ORM: SQLAlchemy
- DB: PostgreSQL
- Auth: JWT
- PDF: WeasyPrint + Jinja2 (HTML/CSS → PDF)
- Tres roles: gerente, operador, cliente
- Ownership: el cliente sólo accede a sus propios recursos (pagos/recibos, facturas)

## Índice

1. Requisitos previos
2. Instalación (entorno y dependencias)
3. Configuración (.env)
4. Estructura del proyecto
5. Modelado de datos (resumen)
6. Seguridad y roles
7. Recibos PDF (plantillas y almacenamiento)
8. Cómo correr en local
9. Documentación y QA (Swagger y Postman)
10. Mantenimiento y evolución
11. Troubleshooting (errores comunes)
12. Roadmap breve
13. Licencia

14. Requisitos previos

---

- Python 3.12+
- PostgreSQL 15+
- Git
- (Windows recomendado) Conda/Miniconda para instalar WeasyPrint
- (Opcional) pgAdmin para administrar la base de datos

2. Instalación (entorno y dependencias)

---

Crear y activar entorno:

conda create -n api_core python=3.12 -y
conda activate api_core

Dependencias backend mínimas:

pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv PyJWT pydantic
pip install "pydantic[email]" # si usas EmailStr en Pydantic

PDF/Plantillas:

conda install -c conda-forge weasyprint tinycss2 cssselect2 -y
pip install jinja2

> Nota Windows: WeasyPrint requiere librerías del sistema; por eso se instala desde conda-forge.

3. Configuración (.env)

---

Crear `backend/.env`:

DATABASE_URL=postgresql+psycopg2://USER:PASS@localhost:5432/isp
JWT_SECRET=cambia_esto_en_produccion
TZ=America/Argentina/Buenos_Aires

Subí un `.env.example` al repo y **no** versionar `.env` real.

4. Estructura del proyecto

---

backend/
app.py # FastAPI app + include_router(...)
auth/
security.py # JWT (generate/verify), fecha/hoy()
roles.py # require_roles(), require_owner_or_roles()
configs/
db.py # engine, SessionLocal, Base, get_db()
models/
modelo.py # TODAS las tablas (SQLAlchemy)
routes/
usuario.py # login, /me, listados admin
cliente.py # ABM clientes
plan.py # ABM planes
contrato.py # ABM contratos + activar/suspender/baja
factura.py # CRUD facturas (admin) + /mi/facturas (cliente)
pago.py # pagos + comprobante + recibo PDF
facturacion.py # datos de empresa (GET/PUT)
assets/
pdf/
receipt.html # plantilla Jinja2 del recibo
style.css # estilos del recibo (A4, layout, tipografías)
storage/
recibos/AAAA/MM/DD/... # PDFs generados (NO versionar)
comprobantes/AAAA/MM/... # archivos subidos (NO versionar)
postman/
UP-Core-\*.postman_collection.json
UP-Core-Local.postman_environment.json
sql/
Usuarios.sql, Clientes.sql, Planes.sql, Contratos.sql, Facturas.sql, Pagos.sql
README.txt
BACKEND_API_DOCS.txt

> Importante:
>
> - Asegurate de agregar `backend/storage/**` al `.gitignore`.
> - La API se levanta desde `backend/` con `uvicorn app:api_upcore --reload`.

5. Modelado de datos (resumen)

---

- Usuario: id, documento?, email?, password_hash, role{gerente|operador|cliente}, activo, creado_en
- Cliente: id, nro_cliente(único), nombre, apellido, documento(único), teléfono, email?, dirección, estado{activo|inactivo}, creado_en
- Plan: id, nombre(único), vel_down, vel_up, precio_mensual, descripcion?, activo, creado_en
- Contrato: id, cliente_id(FK), plan_id(FK), dirección_instalación, fecha_alta, fecha_baja?, estado{borrador|activo|suspendido|baja}, fecha_suspensión?
- Factura (administrativa): id, nro, contrato_id(FK), periodo_mes, periodo_anio, periodo_inicio, periodo_fin, subtotal, mora?, recargo?, total, estado{borrador|emitida|vencida|pagada}, emitida_en?, vencimiento?, pdf_path?
  - Única por (contrato_id, periodo_mes, periodo_anio)
- Pago: id, factura_id(FK), fecha, monto, metodo{efectivo|transferencia}, referencia?, comprobante_path?, estado{registrado|confirmado|anulado}, creado_en, **recibo_path?**
- ConfigFacturacion: company_name, company_dni(CUIT), company_address, company_contact, logo_path?

6. Seguridad y roles

---

- JWT con secret en `.env`. Clase `Security` en `auth/security.py`.
- `auth/roles.py` aporta decoradores sencillos por cabecera `Authorization: Bearer <token>`:
  - `require_roles(headers, {"gerente","operador"})`
  - `require_owner_or_roles(headers, db, allowed_roles={"gerente","operador"})` → valida ownership para clientes.
- Matriz (MVP):
  - Usuarios: admin (listar/paginar/crear)
  - Clientes/Planes/Contratos/Facturas: admin
  - Pagos: admin; clientes pueden subir/descargar sus comprobantes y recibos; y ver `/mi/facturas`.

7. Recibos PDF (plantillas y almacenamiento)

---

- Sólo se generan **recibos de pago** (no facturas PDF).
- Plantillas: `assets/pdf/receipt.html` + `style.css` (editables).
- Rutas de salida: `backend/storage/recibos/AAAA/MM/DD/`
- Nomenclatura: `rec_{DDMMAAAA}_{apellido}_{nombre}_per-{MMAAAA}_p{pagoId}.pdf`
- Se guarda `pago.recibo_path` con la ruta **relativa** para servirlo luego.
- Dependencias: WeasyPrint, Jinja2, tinycss2, cssselect2.
- Datos de empresa (logo, CUIT, dirección…) desde `config_facturacion` (endpoints `/config/facturacion`).

8. Cómo correr en local

---

1. Crear/activar entorno y dependencias (ver §2).
2. Configurar `.env` (ver §3).
3. Crear base y tablas (primera vez):
   - Asegurate de que `models/modelo.py` se ejecute al levantar la app (importa `Base` y crea tablas en `configs/db.py` si corresponde).
   - (Opcional) Correr scripts `sql/*.sql` para cargar datos de prueba.
4. Iniciar servidor:

   cd backend
   uvicorn app:api_upcore --reload

5. Swagger UI: http://127.0.0.1:8000/docs  
   ReDoc: http://127.0.0.1:8000/redoc

9) Documentación y QA (Swagger y Postman)

---

- **Swagger**: todos los endpoints tienen `tags`, `summary` y `description`.
- **Referencia detallada**: ver `BACKEND_API_DOCS.txt`.
- **Postman**: importar las colecciones en `backend/postman/` y el environment `UP-Core-Local.postman_environment.json`.
  Orden sugerido para pruebas:
  1. Usuarios → login (gerente) para obtener `{{token}}`
  2. Planes → crear
  3. Clientes → crear
  4. Contratos → crear
  5. Facturas → crear + emitir
  6. Pagos → crear (con `generar_recibo: true`) → descargar recibo
     - Probar también subir/descargar **comprobante**

10. Mantenimiento y evolución

---

- Cambios de modelo: editar `models/modelo.py` + preparar SQL en `backend/sql/`.
  (Si más adelante agregás Alembic, documentar aquí “alembic revision --autogenerate”)
- Nuevos endpoints: crear/editar en `routes/*.py`, proteger con `require_roles` o `require_owner_or_roles`,
  añadir `summary/description`, actualizar colecciones Postman.
- Storage: **no** versionar `backend/storage/**`. Hacer backups/rotación por carpeta diaria.
- Seguridad: mover `JWT_SECRET` a variables de entorno por entorno (dev/stage/prod).  
  **TODO**: reemplazar `password_hash` plano por hash (p. ej. passlib/bcrypt).
- Performance: usar índices donde filtrás por id/estado/fecha; paginar siempre que la lista crezca.

11. Troubleshooting (errores comunes)

---

- `email-validator is not installed`:  
  → `pip install "pydantic[email]"`
- ImportError `get_db`:
  → revisar import en rutas: `from configs.db import get_db`
- `AttributeError: type object 'Usuario' has no attribute 'routes'`:
  → asegurar que cada router esté creado como `APIRouter()` y se exporte la variable correcta (`Usuario`, `Cliente`, etc.). En `app.py` usar `include_router(Usuario)`, etc.
- WeasyPrint faltante/errores de fuentes:
  → instalar desde conda-forge. Evitar fuentes exóticas; usar sans-serif del sistema.
- 401/403:
  → revisar `Authorization: Bearer <token>` y roles requeridos por endpoint.
- 404 al bajar comprobante/recibo:
  → validar ownership (clientes sólo pueden acceder a sus propios recursos) y que `*_path` referencie un archivo existente en `backend/storage/...`.

12. Roadmap breve

---

- (Corto) Hash de contraseñas; variables secretas por entorno; endpoint `/health`.
- (Medio) Alembic para migraciones; exportación CSV de listados.
- (Futuro) Notificaciones de vencimientos; reglas de recargo configurables.

13. Licencia

---

Uso académico/privado — definir licencia antes de publicación pública.
