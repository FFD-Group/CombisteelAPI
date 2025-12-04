from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    validates,
)


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(primary_key=True)
    uk_price: Mapped[float]
    uk_stock: Mapped[int]
    width: Mapped[int] = mapped_column(nullable=True)
    creation_date: Mapped[int]
    depth: Mapped[int] = mapped_column(nullable=True)
    description: Mapped[str]
    dimensions: Mapped[str] = mapped_column(nullable=True)
    ean: Mapped[str] = mapped_column(nullable=True)
    sku: Mapped[str]
    gross_weight: Mapped[float] = mapped_column(nullable=True)
    height: Mapped[int]
    length: Mapped[int] = mapped_column(nullable=True)
    long_description: Mapped[str] = mapped_column(nullable=True)
    net_weight: Mapped[float] = mapped_column(nullable=True)
    title: Mapped[str]

    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brands.brand_id"), nullable=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.category_id"), nullable=True
    )
    default_image_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("images.image_id"), nullable=True
    )

    images = relationship("ProductImage", back_populates="product")
    default_image = relationship("Image", foreign_keys=[default_image_id])
    brand = relationship("Brand")
    category = relationship("Category")

    @validates("default_image_id")
    def validate_default_image(self, key, image_id):
        if image_id is None:
            return None

        image_ids = {pi.image_id for pi in self.images}

        if image_id not in image_ids:
            raise ValueError(
                f"Image {image_id} is not linked to product {self.product_id}"
            )

        return image_id


class Brand(Base):
    __tablename__ = "brands"

    brand_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True, nullable=False)


class Image(Base):
    __tablename__ = "images"

    image_id: Mapped[int] = mapped_column(primary_key=True)
    creation_date: Mapped[int] = mapped_column(nullable=True)
    filename: Mapped[str] = mapped_column(nullable=False)
    fullpath: Mapped[str] = mapped_column(nullable=False)
    mimetype: Mapped[str] = mapped_column(nullable=True)
    modification_date: Mapped[int] = mapped_column(nullable=True)


class Category(Base):
    __tablename__ = "categories"

    category_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)


class ProductImage(Base):
    __tablename__ = "product_images"

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id"), primary_key=True
    )
    image_id: Mapped[int] = mapped_column(
        ForeignKey("images.image_id"), primary_key=True
    )

    product = relationship("Product", back_populates="images")
    image = relationship("Image")


class ChildProduct(Base):
    __tablename__ = "child_products"

    parent_product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id"), primary_key=True
    )
    child_product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id"), primary_key=True
    )

    parent = relationship("Product", foreign_keys=[parent_product_id])
    child = relationship("Product", foreign_keys=[child_product_id])


class ChildCategory(Base):
    __tablename__ = "child_categories"

    parent_category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.category_id"), primary_key=True
    )
    child_category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.category_id"), primary_key=True
    )

    parent = relationship("Category", foreign_keys=[parent_category_id])
    child = relationship("Category", foreign_keys=[child_category_id])
