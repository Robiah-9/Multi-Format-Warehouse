DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;

CREATE TABLE products (
    product_id   VARCHAR(10)  PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category     VARCHAR(50)  NOT NULL
);

CREATE TABLE reviews (
    review_id   VARCHAR(10) PRIMARY KEY,
    customer_id VARCHAR(10) NOT NULL,
    product_id  VARCHAR(10) NOT NULL REFERENCES products(product_id),
    rating      INTEGER     NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     TEXT,
    review_date DATE        NOT NULL
);

CREATE TABLE orders (
    order_id      VARCHAR(10)   PRIMARY KEY,
    customer_id   VARCHAR(10)   NOT NULL,
    product_id    VARCHAR(10)   NOT NULL REFERENCES products(product_id),
    quantity      INTEGER       NOT NULL CHECK (quantity >= 1),
    unit_price    DECIMAL(10,2) NOT NULL,
    order_date    DATE          NOT NULL,
    price_imputed BOOLEAN       NOT NULL DEFAULT FALSE
);