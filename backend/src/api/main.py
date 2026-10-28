
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.database import Base, engine
from api.models import Product
from api.routes import router as products_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria tabelas ausentes durante o desenvolvimento.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Farma Aura API",
    description="API de cadastro e consulta de produtos.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(products_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
