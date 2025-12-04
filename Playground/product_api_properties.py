from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from dotenv import load_dotenv
from os import getenv
import sys

load_dotenv()

# Select your transport with a defined url endpoint
transport = AIOHTTPTransport(url=getenv("API_URL"))

transport.headers = {
    "content-type": "application/json",
    "X-API-Key": getenv("API_KEY"),
}

# Create a GraphQL client using the defined transport
client = Client(transport=transport)

with open("query.txt", "r") as query_file:
    # Provide a GraphQL query
    raw_query = query_file.read()

    query = gql(raw_query)

# Execute the query on the transport
result = client.execute(query)
with open("output.txt", "w") as output_file:
    product_list = result["getProductListing"]["edges"]
    for node in product_list:
        product = node["node"]
        for key in product.keys():
            try:
                if isinstance(product[key], list) and len(product[key]) == 0:
                    continue
                if product[key] == None:
                    output_file.write(key + ": None\n")
                    continue
                if key in [
                    "defaultImage",
                    "extraImages",
                    "category",
                    "children",
                ]:
                    output_file.write(key + ": " + str(product[key]) + "\n")
                    continue
                else:
                    output_file.write(key + ": " + str(product[key]) + "\n")
            except Exception as e:
                print(e)
                print("handling", key, "caused exception")
                print("node:", node)
                sys.exit(1)
        output_file.write("---------------------------------------------\n\n")
