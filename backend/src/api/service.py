
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.models import Product
from api.schemas import ProductCreate, ProductUpdate


def create_product(db: Session, data: ProductCreate) -> Product:
    product = Product(**data.model_dump())

    try:
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    except Exception:
        db.rollback()
        raise


def list_products(db: Session) -> list[Product]:
    statement = select(Product).order_by(Product.id)
    return list(db.scalars(statement).all())


def get_product(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def update_product(
    db: Session,
    product: Product,
    data: ProductUpdate,
) -> Product:
    changes = data.model_dump(exclude_unset=True)

    for field, value in changes.items():
        if value is not None:
            setattr(product, field, value)

    try:
        db.commit()
        db.refresh(product)
        return product
    except Exception:
        db.rollback()
        raise


def delete_product(db: Session, product: Product) -> None:
    try:
        db.delete(product)
        db.commit()
    except Exception:
        db.rollback()
        raise
