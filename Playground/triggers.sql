----------------------------------------------------
-- Trigger: on INSERT
----------------------------------------------------
CREATE TRIGGER trg_product_default_image_insert
AFTER INSERT ON Product
WHEN NEW.defaultImageId IS NOT NULL
BEGIN
    SELECT
        CASE
            WHEN NOT EXISTS (
                SELECT 1
                FROM ProductImage
                WHERE productId = NEW.productId
                  AND imageId   = NEW.defaultImageId
            )
            THEN RAISE(ABORT, 'defaultImageId must reference an image linked to this product')
        END;
END;

----------------------------------------------------
-- Trigger: on UPDATE of defaultImageId
----------------------------------------------------
CREATE TRIGGER trg_product_default_image_update
AFTER UPDATE OF defaultImageId ON Product
WHEN NEW.defaultImageId IS NOT NULL
BEGIN
    SELECT
        CASE
            WHEN NOT EXISTS (
                SELECT 1
                FROM ProductImage
                WHERE productId = NEW.productId
                  AND imageId   = NEW.defaultImageId
            )
            THEN RAISE(ABORT, 'defaultImageId must reference an image linked to this product')
        END;
END;
