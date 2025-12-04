from sqlalchemy.orm import Session
from Engine import engine
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


class QueryManager:
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


if __name__ == "__main__":
    qm = QueryManager()
    count = 1
    for product in qm.get_products():
        print(product)
        count += 1
    print(count, "products fetched from API.")
