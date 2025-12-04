-- Always enable foreign keys in SQLite
PRAGMA foreign_keys = ON;

----------------------------------------------------
-- Brand
----------------------------------------------------
CREATE TABLE Brand (
    brandId     INTEGER PRIMARY KEY,
    name        TEXT NOT NULL
);

----------------------------------------------------
-- Category
----------------------------------------------------
CREATE TABLE Category (
    categoryId  INTEGER PRIMARY KEY,
    name        TEXT NOT NULL
);

----------------------------------------------------
-- Image
----------------------------------------------------
CREATE TABLE Image (
    imageId          INTEGER PRIMARY KEY,
    creationDate     INTEGER,     -- e.g. unix timestamp
    filename         TEXT NOT NULL,
    fullpath         TEXT NOT NULL,
    mimetype         TEXT,
    modificationDate INTEGER
);

----------------------------------------------------
-- Product
----------------------------------------------------
CREATE TABLE Product (
    productId       INTEGER PRIMARY KEY,
    ukPrice         REAL,
    ukStock         INTEGER,
    brandId         INTEGER,      -- FK → Brand
    categoryId      INTEGER,      -- FK → Category
    creationDate    INTEGER,
    defaultImageId  INTEGER,      -- default Image for this Product
    width           INTEGER,
    height          INTEGER,
    depth           INTEGER,
    length          INTEGER,
    grossWeight     REAL,
    netWeight       REAL,
    dimensions      TEXT,
    description     TEXT,
    longDescription TEXT,
    ean             TEXT,
    sku             TEXT,
    title           TEXT,

    -- Foreign keys
    FOREIGN KEY (brandId)        REFERENCES Brand(brandId),
    FOREIGN KEY (categoryId)     REFERENCES Category(categoryId),
    FOREIGN KEY (defaultImageId) REFERENCES Image(imageId),

    UNIQUE (sku),
    UNIQUE (ean)
);

----------------------------------------------------
-- ProductImage: link between Products and Images
----------------------------------------------------
CREATE TABLE ProductImage (
    productId  INTEGER NOT NULL,
    imageId    INTEGER NOT NULL,

    PRIMARY KEY (productId, imageId),

    FOREIGN KEY (productId) REFERENCES Product(productId)
        ON DELETE CASCADE,
    FOREIGN KEY (imageId)   REFERENCES Image(imageId)
        ON DELETE CASCADE
);

-- Helpful indexes (composite PK already covers (productId, imageId))
CREATE INDEX idx_productimage_image ON ProductImage(imageId);

----------------------------------------------------
-- ChildProduct: parent/child product relationships
----------------------------------------------------
CREATE TABLE ChildProduct (
    childProductId  INTEGER NOT NULL,
    parentProductId INTEGER NOT NULL,

    PRIMARY KEY (childProductId, parentProductId),

    FOREIGN KEY (childProductId)  REFERENCES Product(productId)
        ON DELETE CASCADE,
    FOREIGN KEY (parentProductId) REFERENCES Product(productId)
        ON DELETE CASCADE
);

----------------------------------------------------
-- ChildCategory: parent/child category relationships
----------------------------------------------------
CREATE TABLE ChildCategory (
    childCategoryId  INTEGER NOT NULL,
    parentCategoryId INTEGER NOT NULL,

    PRIMARY KEY (childCategoryId, parentCategoryId),

    FOREIGN KEY (childCategoryId)  REFERENCES Category(categoryId)
        ON DELETE CASCADE,
    FOREIGN KEY (parentCategoryId) REFERENCES Category(categoryId)
        ON DELETE CASCADE
);
