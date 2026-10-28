
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=200)
    principio_ativo: str = Field(min_length=2, max_length=150)
    concentracao: str = Field(min_length=1, max_length=100)
    apresentacao: str = Field(min_length=2, max_length=150)


class ProductUpdate(BaseModel):
    nome: str | None = Field(
        default=None, min_length=2, max_length=200
    )
    principio_ativo: str | None = Field(
        default=None, min_length=2, max_length=150
    )
    concentracao: str | None = Field(
        default=None, min_length=1, max_length=100
    )
    apresentacao: str | None = Field(
        default=None, min_length=2, max_length=150
    )


class ProductRead(BaseModel):
    id: int
    nome: str
    principio_ativo: str
    concentracao: str
    apresentacao: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
