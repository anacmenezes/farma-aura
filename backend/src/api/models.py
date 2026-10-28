
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from api.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    nome: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    principio_ativo: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    concentracao: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    apresentacao: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
