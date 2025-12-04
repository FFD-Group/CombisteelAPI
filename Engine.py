from sqlalchemy import create_engine
from dotenv import load_dotenv
from os import getenv

load_dotenv()

database_name = getenv("DATABASE_NAME", "database.db")
engine = create_engine(f"sqlite:///{database_name}")


def create_tables(db_engine=engine):
    """
    Create the tables for all `Base` derived models.
    """
    from Models import Base

    Base.metadata.create_all(db_engine)


def create_test_entities():
    """
    Created linked test entities in the test database.
    """
    from sqlalchemy.orm import Session
    from Models import (
        Brand,
        Image,
        Category,
        Product,
        ProductImage,
        ChildCategory,
        ChildProduct,
    )

    test_engine = create_engine("sqlite:///test_database.db", echo=True)

    create_tables(test_engine)

    with Session(test_engine) as session:
        # 1) Create entities
        brand = Brand(name="Acme")
        image = Image(
            creation_date=1764842719,
            filename="product_image.jpg",
            fullpath="images/product_image.jpg",
            mimetype="image/jpeg",
            modification_date=1764842719,
        )
        fridges_category = Category(name="Fridges")
        refrigeration_category = Category(name="Refrigeration")

        session.add_all(
            [brand, image, fridges_category, refrigeration_category]
        )
        session.flush()

        test_product = Product(
            uk_price=500.45,
            uk_stock=325,
            width=600,
            creation_date=1764842719,
            depth=500,
            description="My test product",
            dimensions="1800x600x500(HxWxD)",
            ean=None,
            sku="7000.1234",
            gross_weight=100.34,
            height=1800,
            length=None,
            long_description="My test product is a bog standard fridge shaped test product that I can test with.",
            net_weight=80.54,
            title="My test product",
            brand_id=brand.brand_id,
            category_id=fridges_category.category_id,
        )

        child_product = Product(
            uk_price=35.00,
            uk_stock=1300,
            width=450,
            creation_date=1764842719,
            depth=400,
            description="My test shelf",
            dimensions="15x450x400(HxWxD)",
            ean=None,
            sku="7000.1235",
            gross_weight=0.25,
            height=15,
            length=None,
            long_description=None,
            net_weight=0.21,
            title="My test shelf",
            brand_id=brand.brand_id,
            category_id=refrigeration_category.category_id,
        )

        session.add_all([test_product, child_product])
        session.flush()
        # 2) Create entity link records
        product_image_link = ProductImage(
            product_id=test_product.product_id, image_id=image.image_id
        )
        child_category = ChildCategory(
            parent_category_id=refrigeration_category.category_id,
            child_category_id=fridges_category.category_id,
        )
        child_product = ChildProduct(
            parent_product_id=test_product.product_id,
            child_product_id=child_product.product_id,
        )

        session.add_all([product_image_link, child_category, child_product])
        session.flush()
        # 3) Create relationships that rely on link records
        test_product.default_image_id = image.image_id

        session.commit()


if __name__ == "__main__":
    create_test_entities()
