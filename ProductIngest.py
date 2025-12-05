from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import select
from Engine import engine, create_tables
from Models import (
    Product,
    Brand,
    Image,
    Category,
    ProductImage,
    ChildCategory,
    ChildProduct,
)

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from gql.transport.exceptions import TransportServerError
from dotenv import load_dotenv
from os import getenv
import time

load_dotenv()


class ApiQueryManager:
    """Manage a set of queries to the API"""

    def __init__(self):
        """Initialise the GraphQl query, pagination and other variables"""
        self._transport = AIOHTTPTransport(url=getenv("API_URL"))
        self._transport.headers = {
            "content-type": "application/json",
            "X-API-Key": getenv("API_KEY"),
        }
        # Create a GraphQL client using the defined transport
        self._client = Client(transport=self._transport)
        self._page_size = 100
        self._has_more = True
        self._offset = 0
        self._total_count = None
        self._backoff_initial = 1.0  # seconds
        self._max_retries = 5
        self._query = gql(
            """
            query ($first: Int!, $after: Int) {
                getProductListing(defaultLanguage: "en", first: $first, after: $after) {
                    totalCount
                    edges {
                        node {
                            sku
                            description
                            brand
                            category {
                                ... on object_Category {
                                    name
                                    parent {
                                        ... on object_Category {
                                            name
                                        }
                                    }
                                    children {
                                        ... on object_Category {
                                            name
                                        }
                                    }
                                }
                            }
                            depth
                            ean
                            dimensions
                            height
                            grossWeight
                            extraImages {
                                image {
                                    creationDate
                                    filename
                                    fullpath
                                    mimetype
                                    modificationDate
                                }
                            }
                            length
                            longDescription
                            netWeight
                            title
                            ukPrice
                            ukStock
                            width
                            children {
                                ... on object_Product {
                                    sku
                                }
                            }
                            defaultImage {
                                creationDate
                                filename
                                fullpath
                                mimetype
                                modificationDate
                            }
                            creationDate
                        }
                    }
                }
            }
            """
        )
        self._current_products = iter([])

    def _query_page(self):
        """
        Query for the next page of results from the API.
        """
        retries = 0
        delay = self._backoff_initial
        while True:
            try:
                response = self._client.execute(
                    self._query,
                    variable_values={
                        "first": self._page_size,
                        "after": self._offset,
                    },
                )
                break
            except TransportServerError as exc:
                status = (
                    getattr(exc, "code", None)
                    or getattr(exc, "status_code", None)
                    or getattr(exc, "http_status", None)
                )
                if (
                    status == 429 or "429" in str(exc)
                ) and retries < self._max_retries:
                    time.sleep(delay)
                    retries += 1
                    delay *= 2
                    continue
                raise
        data = response["getProductListing"]
        edges = data.get("edges", [])
        if self._total_count is None:
            self._total_count = data.get("totalCount", 0)
        self._offset += len(edges)
        self._has_more = len(edges) > 0 and self._offset < self._total_count
        self._current_products = iter(edges)

    def get_products(self):
        """
        Yield the generator of products from the API
        """
        while True:
            try:
                product = next(self._current_products)
                yield product["node"]
            except StopIteration:
                if not self._has_more:
                    break
                self._query_page()


class DatabaseFacade:
    """Interact with the database entities."""

    def __init__(self, engine):
        """Set up instance properties."""
        self._engine = engine
        # session factory with expire_on_commit disabled to avoid detaching objects
        self._Session = sessionmaker(bind=self._engine, expire_on_commit=False)

    def find_product(self, sku: str) -> Product | None:
        """Find a Product in the database with the given sku."""
        stmt = select(Product).where(Product.sku.in_([sku]))
        with self._Session() as session:
            return session.scalar(stmt)

    def add_product(self, product: Product) -> Product:
        """Add a Product to the database using the given entity."""
        with self._Session() as session:
            session.add(product)
            session.commit()
            return product

    def find_brand(self, brand: str) -> Brand | None:
        """Find a Brand in the database with the given name."""
        stmt = select(Brand).where(Brand.name.in_([brand]))
        with self._Session() as session:
            return session.scalar(stmt)

    def add_brand(self, brand: str) -> Brand:
        """Add a Brand to the database with the given name."""
        brand_entity = Brand(name=brand)
        with self._Session() as session:
            session.add(brand_entity)
            session.commit()
            return brand_entity

    def associate_brand(self, product: Product, brand: Brand) -> None:
        """Associate the given Product with the given Brand."""
        with self._Session() as session:
            product = session.merge(product)
            product.brand_id = brand.brand_id
            session.commit()

    def find_category(self, category: dict) -> Category | None:
        """Find a Category in the database with the given name."""
        category_name = category["name"]
        stmt = select(Category).where(Category.name.is_(category_name))
        with self._Session() as session:
            return session.scalar(stmt)

    def add_category(self, category: dict) -> Category:
        """Add a Category to the database using the given entity."""
        category_name = category["name"]
        category_entity = Category(name=category_name)
        if category["parent"]:
            parent_category_name = category["parent"]["name"]
            parent_category_entity = Category(name=parent_category_name)
        with self._Session() as session:
            session.add(category_entity)
            if parent_category_entity:
                session.add(parent_category_entity)
            session.commit()
            return category_entity

    def associate_category(self, product: Product, category: Category) -> None:
        """Associate the given Product with the given Category."""
        with self._Session() as session:
            product = session.merge(product)
            product.category_id = category.category_id
            session.commit()

    def find_image(self, image: dict) -> Image | None:
        """Find an Image in the database with the given fullpath."""
        if "image" in image:
            fullpath = image["image"]["fullpath"]
        else:
            fullpath = image["fullpath"]
        stmt = select(Image).where(Image.fullpath.in_([fullpath]))
        with self._Session() as session:
            return session.scalar(stmt)

    def add_image(self, image: dict) -> Image:
        """Add an Image to the database using the given entity."""
        if "image" in image:
            image = image["image"]
        image_entity = Image(
            creation_date=image["creationDate"],
            filename=image["filename"],
            fullpath=image["fullpath"],
            mimetype=image["mimetype"],
            modification_date=image["modificationDate"],
        )
        with self._Session() as session:
            session.add(image_entity)
            session.commit()
            return image_entity

    def associate_image(
        self, product: Product, image: Image, is_default=False
    ) -> None:
        with self._Session() as session:
            # Attach product to this session and ensure relationship is populated
            product_in_session = session.merge(product)
            product_image_link = ProductImage(
                product_id=product_in_session.product_id,
                image_id=image.image_id,
            )
            # add via relationship so validate_default_image sees the link
            product_in_session.images.append(product_image_link)
            if is_default:
                product_in_session.default_image_id = image.image_id
            session.commit()


if __name__ == "__main__":
    qm = ApiQueryManager()
    df = DatabaseFacade(engine)
    create_tables(engine)
    total_count = 1
    added_count = 0
    brands_count = 0
    category_count = 0
    image_count = 0
    for product in qm.get_products():
        if not df.find_product(product["sku"]):
            # Product creation
            p = Product(
                uk_price=product["ukPrice"],
                uk_stock=product["ukStock"],
                width=product["width"],
                creation_date=product["creationDate"],
                depth=product["depth"],
                description=product["description"],
                dimensions=product["dimensions"],
                ean=product["ean"],
                sku=product["sku"],
                gross_weight=product["grossWeight"],
                height=product["height"],
                length=product["length"],
                long_description=product["longDescription"],
                net_weight=product["netWeight"],
                title=product["title"],
            )
            added_p = df.add_product(p)
            added_count += 1
            # Brand assocation/creation
            product_brand = product["brand"]
            if product_brand:
                existing_brand = df.find_brand(product_brand)
                if not existing_brand:
                    existing_brand = df.add_brand(product_brand)
                    brands_count += 1
                df.associate_brand(added_p, existing_brand)
            # Category association/creation
            product_categories = product["category"]
            if product_categories and len(product_categories) > 0:
                for product_category in product_categories:
                    existing_category = df.find_category(product_category)
                    if not existing_category:
                        existing_category = df.add_category(product_category)
                        category_count += 1
                    df.associate_category(added_p, existing_category)
            # Image creation/association
            product_extra_images = product["extraImages"]
            product_default_image = product["defaultImage"]
            if product_extra_images and len(product_extra_images) > 0:
                for product_image in product_extra_images:
                    existing_image = df.find_image(product_image)
                    if not existing_image:
                        existing_image = df.add_image(product_image)
                        image_count += 1
                    df.associate_image(added_p, existing_image)
            if product_default_image:
                existing_image = df.find_image(product_default_image)
                if not existing_image:
                    existing_image = df.add_image(product_default_image)
                    image_count += 1
                df.associate_image(added_p, existing_image, True)

        total_count += 1
    print(
        total_count,
        "products fetched from API.",
        added_count,
        "added to database.",
    )
    print(
        brands_count,
        "brands,",
        category_count,
        "categories,",
        image_count,
        "images.",
    )
    print('Finding Product "7950.5345": ', df.find_product("7950.5345"))
