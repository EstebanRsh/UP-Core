# models/modelo.py
from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    Text,
    Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from configs.db import Base


# -----------------------------
# Enums
# -----------------------------
class RoleEnum(str, Enum):
    gerente = "gerente"
    operador = "operador"
    cliente = "cliente"


class EstadoClienteEnum(str, Enum):
    activo = "activo"
    inactivo = "inactivo"


class EstadoContratoEnum(str, Enum):
    borrador = "borrador"
    activo = "activo"
    suspendido = "suspendido"
    baja = "baja"


class EstadoFacturaEnum(str, Enum):
    borrador = "borrador"
    emitida = "emitida"
    vencida = "vencida"
    pagada = "pagada"


class MetodoPagoEnum(str, Enum):
    efectivo = "efectivo"
    transferencia = "transferencia"


class EstadoPagoEnum(str, Enum):
    registrado = "registrado"
    confirmado = "confirmado"
    anulado = "anulado"


# -----------------------------
# Usuario (auth)
# -----------------------------
class Usuario(Base):
    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True)
    # DNI/CUIT normalizado; puede ser NULL si sólo usa email
    documento = Column(String(11), unique=True, index=True, nullable=True)
    email = Column(String(120), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(RoleEnum, name="role_enum"), index=True, nullable=False)
    activo = Column(Boolean, default=True, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)


# -----------------------------
# Cliente
# -----------------------------
class Cliente(Base):
    __tablename__ = "cliente"

    id = Column(Integer, primary_key=True)
    nro_cliente = Column(
        String(16), unique=True, index=True, nullable=False
    )  # lo generamos en servicio
    nombre = Column(String(80), nullable=False)
    apellido = Column(String(80), nullable=False)
    documento = Column(String(11), unique=True, index=True, nullable=False)
    telefono = Column(String(20), nullable=True)  # +549...
    email = Column(String(120), nullable=True)
    direccion = Column(String(200), nullable=False)
    estado = Column(
        SAEnum(EstadoClienteEnum, name="estado_cliente_enum"),
        nullable=False,
        default=EstadoClienteEnum.activo.value,
    )
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    contratos = relationship("Contrato", back_populates="cliente")


# -----------------------------
# Plan
# -----------------------------
class Plan(Base):
    __tablename__ = "plan"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(120), unique=True, index=True, nullable=False)
    vel_down = Column(Integer, nullable=False)  # Mbps
    vel_up = Column(Integer, nullable=False)  # Mbps
    precio_mensual = Column(Numeric(12, 2), nullable=False)  # ARS
    descripcion = Column(Text, nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    contratos = relationship("Contrato", back_populates="plan")


# -----------------------------
# Contrato
# -----------------------------
class Contrato(Base):
    __tablename__ = "contrato"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(
        Integer,
        ForeignKey("cliente.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    plan_id = Column(
        Integer, ForeignKey("plan.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    direccion_instalacion = Column(String(200), nullable=False)
    fecha_alta = Column(Date, nullable=False)
    fecha_baja = Column(Date, nullable=True)
    estado = Column(
        SAEnum(EstadoContratoEnum, name="estado_contrato_enum"),
        nullable=False,
        default=EstadoContratoEnum.borrador.value,
    )
    fecha_suspension = Column(Date, nullable=True)

    cliente = relationship("Cliente", back_populates="contratos")
    plan = relationship("Plan", back_populates="contratos")
    facturas = relationship("Factura", back_populates="contrato")


# -----------------------------
# Factura
# -----------------------------
class Factura(Base):
    __tablename__ = "factura"

    id = Column(Integer, primary_key=True)
    nro = Column(
        String(32), unique=True, index=True, nullable=False
    )  # lo generamos en servicio
    contrato_id = Column(
        Integer,
        ForeignKey("contrato.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    periodo_mes = Column(Integer, nullable=False)  # 1..12
    periodo_anio = Column(Integer, nullable=False)  # ej. 2025
    periodo_inicio = Column(Date, nullable=False)
    periodo_fin = Column(Date, nullable=False)

    subtotal = Column(Numeric(12, 2), nullable=False)
    mora = Column(Numeric(12, 2), nullable=True)
    recargo = Column(Numeric(12, 2), nullable=True)
    total = Column(Numeric(12, 2), nullable=False)

    estado = Column(
        SAEnum(EstadoFacturaEnum, name="estado_factura_enum"),
        nullable=False,
        default=EstadoFacturaEnum.borrador.value,
    )
    emitida_en = Column(DateTime, nullable=True)
    vencimiento = Column(Date, nullable=True)
    pdf_path = Column(String(300), nullable=True)

    contrato = relationship("Contrato", back_populates="facturas")
    pagos = relationship("Pago", back_populates="factura")


# -----------------------------
# Pago
# -----------------------------
class Pago(Base):
    __tablename__ = "pago"

    id = Column(Integer, primary_key=True)
    factura_id = Column(
        Integer,
        ForeignKey("factura.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False)
    monto = Column(Numeric(12, 2), nullable=False)
    metodo = Column(SAEnum(MetodoPagoEnum, name="metodo_pago_enum"), nullable=False)
    referencia = Column(String(80), nullable=True)  # nro de transferencia, etc.
    comprobante_path = Column(String(300), nullable=True)  # ruta al archivo subido
    estado = Column(
        SAEnum(EstadoPagoEnum, name="estado_pago_enum"),
        nullable=False,
        default=EstadoPagoEnum.registrado.value,
    )
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    factura = relationship("Factura", back_populates="pagos")
