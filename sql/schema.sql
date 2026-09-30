-- ============================================================
-- Mamaearth Returns & Growth Intelligence Pipeline
-- Part 1 / Task 1 -- Relational schema
-- ============================================================
-- Three tables: customers, products, orders.
-- discount_pct and rating are deliberately NOT NOT-NULL: a real
-- order can be un-rated (customer hasn't rated yet) or have no
-- promo code applied. NULL is the correct representation of
-- "unknown / not given", not an error to constrain away.

DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id         VARCHAR(10)  PRIMARY KEY,
    name                 VARCHAR(50)  NOT NULL,
    city                 VARCHAR(50)  NOT NULL,
    city_tier            INT          NOT NULL,
    signup_date           DATE         NOT NULL,
    acquisition_source    VARCHAR(20)  NOT NULL
);

CREATE TABLE products (
    product_id      VARCHAR(10)     PRIMARY KEY,
    product_name    VARCHAR(100)    NOT NULL,
    category        VARCHAR(30)     NOT NULL,
    price           DECIMAL(10,2)   NOT NULL
);

CREATE TABLE orders (
    order_id         VARCHAR(10)   PRIMARY KEY,
    customer_id      VARCHAR(10)   NOT NULL,
    product_id       VARCHAR(10)   NOT NULL,
    order_date       DATE          NOT NULL,
    quantity         INT           NOT NULL,
    discount_pct     INT,                       -- NULL = no promo code applied
    payment_method   VARCHAR(10)   NOT NULL,
    rating           INT,                        -- NULL = not yet rated
    returned         INT           NOT NULL DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (product_id)  REFERENCES products(product_id)
);
