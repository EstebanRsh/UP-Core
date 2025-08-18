import sys

sys.tracebacklimit = 1
from fastapi import FastAPI
from routes.usuario import Usuario
from routes.cliente import Cliente
from routes.plan import Plan
from routes.contrato import Contrato
from routes.factura import Factura
from fastapi.middleware.cors import CORSMiddleware

api_upcore = FastAPI()


@api_upcore.get("/")
def helloworld():
    return "hello world"


api_upcore.include_router(Usuario)
api_upcore.include_router(Cliente)
api_upcore.include_router(Plan)
api_upcore.include_router(Contrato)
api_upcore.include_router(Factura)


api_upcore.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# conda activate api_core

# uvicorn app:api_upcore --reload
