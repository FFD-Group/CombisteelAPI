import sqlite3

# Create or open the DB
conn = sqlite3.connect("products_schema_test.db")
cur = conn.cursor()

# Enable foreign keys
cur.execute("PRAGMA foreign_keys = ON;")

# -------------------------
# Create schema
# -------------------------
with open("ddl.sql", "r") as ddl_file:
    schema = ddl_file.read()

cur.executescript(schema)
conn.commit()

# -------------------------
# Insert example data
# -------------------------

# Brand and Category
cur.execute("INSERT INTO Brand (brandId, name) VALUES (?, ?)", (1, "Acme"))
cur.execute(
    "INSERT INTO Category (categoryId, name) VALUES (?, ?)", (10, "Tools")
)

# Product (no default image yet)
cur.execute(
    """
    INSERT INTO Product (productId, brandId, categoryId, title, sku)
    VALUES (?, ?, ?, ?, ?)
""",
    (100, 1, 10, "Hammer Deluxe", "HAM-123"),
)

# Two image rows
cur.execute(
    """
    INSERT INTO Image (imageId, filename, fullpath)
    VALUES (?, ?, ?)
""",
    (200, "hammer-front.jpg", "/img/hammer-front.jpg"),
)

cur.execute(
    """
    INSERT INTO Image (imageId, filename, fullpath)
    VALUES (?, ?, ?)
""",
    (201, "hammer-side.jpg", "/img/hammer-side.jpg"),
)

# Link images to product
cur.execute(
    "INSERT INTO ProductImage (productId, imageId) VALUES (?, ?)", (100, 200)
)
cur.execute(
    "INSERT INTO ProductImage (productId, imageId) VALUES (?, ?)", (100, 201)
)

conn.commit()

print("\nSetting default image to a valid one (should succeed)…")
cur.execute(
    """
    UPDATE Product SET defaultImageId = ? WHERE productId = ?
""",
    (200, 100),
)
conn.commit()
print("✓ Success!")

print("\nSetting default image to an unrelated image (should fail)…")
try:
    cur.execute(
        """
        UPDATE Product SET defaultImageId = ? WHERE productId = ?
    """,
        (999, 100),
    )
    conn.commit()
except Exception as e:
    print("✗ Error:", e)

conn.close()
