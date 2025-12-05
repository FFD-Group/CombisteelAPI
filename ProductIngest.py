from sqlalchemy.orm import Session
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
        self._session = Session(self._engine)

    def find_product(self, sku: str) -> Product | None:
        stmt = select(Product).where(Product.sku.in_([sku]))
        with self._session as session:
            return session.scalar(stmt)

    def add_product(self, product: Product) -> Product:
        with self._session as session:
            session.add(product)
            session.commit()
            return Product

    def find_brand(self, brand: str) -> Brand | None:
        pass

    def add_brand(self, brand: str) -> Brand:
        pass

    def associate_brand(self, product: Product, brand: Brand) -> None:
        pass

    # EXAMPLE CATEGORY OBJ
    # {
    #     "name": "Voorraadkasten",
    #     "parent": {
    #         "name": "Wand- en voorraadkasten"
    #     },
    #     "children": []
    # }
    def find_category(self, category: dict) -> Category | None:
        pass

    def add_category(self, category: dict) -> Category:
        pass

    def associate_category(self, product: Product, category: Category) -> None:
        pass

    # EXAMPLE IMAGE OBJ
    # [
    #     {
    #         "image": {
    #             "creationDate": 1753856708,
    #             "filename": "7003.0700-0701-0702-0703a_3.jpg",
    #             "fullpath": "/Product%20Assets/7003.0700-0701-0702-0703a_3.jpg",
    #             "mimetype": "image/jpeg",
    #             "modificationDate": 1753856708
    #         }
    #     }
    # ]
    def find_image(self, image: dict) -> Image | None:
        pass

    def add_image(self, image: dict) -> Image:
        pass

    def associate_image(
        self, product: Product, image: Image, is_default=False
    ) -> None:
        pass


if __name__ == "__main__":
    qm = ApiQueryManager()
    df = DatabaseFacade(engine)
    create_tables(engine)
    total_count = 1
    added_count = 0
    categories = {}
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
                df.associate_brand(added_p, existing_brand)
            # Category association/creation
            product_categories = product["category"]
            if len(product_categories) > 0:
                for product_category in product_categories:
                    existing_category = df.find_category(product_category)
                    if not existing_category:
                        existing_category = df.add_category(product_category)
                    df.associate_category(added_p, existing_category)
            # Image creation/association
            product_extra_images = product["extraImages"]
            product_default_image = product["defaultImage"]
            if len(product_extra_images) > 0:
                for product_image in product_extra_images:
                    existing_image = df.find_image(product_image)
                    if not existing_image:
                        existing_image = df.add_image(product_image)
                    df.associate_image(added_p, existing_image)
            if product_default_image:
                existing_image = df.find_image(product_default_image)
                if not existing_image:
                    existing_image = df.add_image(product_default_image)
                df.associate_image(added_p, existing_image, True)

        total_count += 1
    print(
        total_count,
        "products fetched from API.",
        added_count,
        "added to database.",
    )
    print(df.find_product("7950.5345"))
