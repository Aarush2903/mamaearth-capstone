-- ============================================================
-- Part 1 / Task 3 -- Reports
-- Run against the loaded, RAW (uncleaned) data.
-- Every query below was executed against SQLite loaded from
-- schema.sql + seed_data.sql. Actual output is pasted as a
-- comment directly above each query, exactly as produced.
-- ============================================================


-- ------------------------------------------------------------
-- (a) Order totals
-- revenue per row = quantity * price * (1 - discount_pct/100),
-- NULL discount treated as 0% via COALESCE.
--
-- Output:
-- total_orders | total_revenue | avg_order_value
-- 180          | 99860.20      | 554.78
-- ------------------------------------------------------------
SELECT
    COUNT(*) AS total_orders,
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_revenue,
    ROUND(AVG(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS avg_order_value
FROM orders o
JOIN products p ON o.product_id = p.product_id;


-- ------------------------------------------------------------
-- (b) COUNT(*) vs COUNT(column)
-- Shows how many orders are missing a rating.
--
-- Output:
-- total_rows | rated_rows | missing_ratings
-- 180        | 165        | 15
-- ------------------------------------------------------------
SELECT
    COUNT(*)              AS total_rows,
    COUNT(rating)          AS rated_rows,
    COUNT(*) - COUNT(rating) AS missing_ratings
FROM orders;


-- ------------------------------------------------------------
-- (c) LEFT JOIN zero-match row, confirmed independently
-- Finds the one customer with no orders at all.
--
-- Query 1 (LEFT JOIN) output:
-- customer_id | name   | order_count
-- C045        | Vihaan | 0
-- ------------------------------------------------------------
SELECT
    c.customer_id,
    c.name,
    COUNT(o.order_id) AS order_count
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
HAVING COUNT(o.order_id) = 0;

-- Query 2 (independent NOT IN check) output:
-- customer_id | name
-- C045        | Vihaan
-- Confirms query 1: both return exactly the same single row,
-- so the LEFT JOIN result is trusted rather than assumed.
-- ------------------------------------------------------------
SELECT customer_id, name
FROM customers
WHERE customer_id NOT IN (SELECT DISTINCT customer_id FROM orders);


-- ------------------------------------------------------------
-- (d) GROUP BY + HAVING -- return rate by city, > 20%
--
-- Output (exactly 3 rows, ordered by return_rate_pct DESC):
-- city      | total_orders | returned_orders | return_rate_pct
-- Jaipur    | 19           | 8               | 42.1
-- Lucknow   | 49           | 15              | 30.6
-- Bangalore | 33           | 8               | 24.2
-- (Mumbai 17.9% and Delhi 17.4% correctly excluded by HAVING.)
-- ------------------------------------------------------------
SELECT
    c.city,
    COUNT(o.order_id) AS total_orders,
    SUM(o.returned)    AS returned_orders,
    ROUND(100.0 * SUM(o.returned) / COUNT(o.order_id), 1) AS return_rate_pct
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING return_rate_pct > 20
ORDER BY return_rate_pct DESC;


-- ------------------------------------------------------------
-- (e) Ranking with ORDER BY + LIMIT/OFFSET
-- Tie-break on customer_id ASC: two customers could tie on
-- total_spend, and without a secondary key ties would be
-- ordered arbitrarily by the engine, making the ranking
-- non-reproducible across runs/engines. customer_id ASC gives
-- a fully deterministic order.
--
-- Query 1 (LIMIT 5) output:
-- customer_id | name    | total_spend
-- C043        | Reyansh | 12920.00
-- C026        | Isha    | 8371.60
-- C008        | Meera   | 4564.60
-- C011        | Arjun   | 4111.00
-- C042        | Sanya   | 3785.00
-- ------------------------------------------------------------
SELECT
    c.customer_id,
    c.name,
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_spend
FROM orders o
JOIN products p  ON o.product_id = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 5;

-- Query 2 (LIMIT 3 OFFSET 2 -- ranks 3 to 5, no re-deriving top 5) output:
-- customer_id | name    | total_spend
-- C008        | Meera   | 4564.60
-- C011        | Arjun   | 4111.00
-- C042        | Sanya   | 3785.00
-- Matches the last three rows of query 1 exactly, same order.
-- ------------------------------------------------------------
SELECT
    c.customer_id,
    c.name,
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_spend
FROM orders o
JOIN products p  ON o.product_id = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 3 OFFSET 2;


-- ------------------------------------------------------------
-- (f) Three-table JOIN with GROUP BY -- revenue by category
-- orders + products + customers joined (customers isn't
-- strictly needed for this aggregation, but included to
-- confirm the three-way join compiles cleanly, since Part 3
-- relies on the same join shape).
--
-- Output (ordered by category_revenue DESC):
-- category     | order_count | category_revenue
-- Haircare     | 54          | 44956.10
-- Skincare     | 60          | 27346.00
-- Babycare     | 30          | 16805.00
-- PersonalCare | 36          | 10753.10
-- ------------------------------------------------------------
SELECT
    p.category,
    COUNT(o.order_id) AS order_count,
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS category_revenue
FROM orders o
JOIN products p  ON o.product_id = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY p.category
ORDER BY category_revenue DESC;


-- ------------------------------------------------------------
-- (g) LIKE pattern match -- names starting with 'A'
--
-- Output:
-- count
-- 10
-- ------------------------------------------------------------
SELECT COUNT(*) AS customers_starting_with_a
FROM customers
WHERE name LIKE 'A%';


-- ------------------------------------------------------------
-- (h) DISTINCT acquisition sources
--
-- Output (4 distinct values):
-- Organic, Referral, Ad, Social
-- ------------------------------------------------------------
SELECT DISTINCT acquisition_source
FROM customers;


-- ------------------------------------------------------------
-- (i) ALTER TABLE + UPDATE with CASE
-- Every customer gets a loyalty_tier: Tier-1 city -> Gold,
-- everyone else -> Silver. No WHERE clause -- all rows updated.
-- ------------------------------------------------------------
ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(10);

UPDATE customers
SET loyalty_tier = CASE WHEN city_tier = 1 THEN 'Gold' ELSE 'Silver' END;

-- Verification output:
-- loyalty_tier | count
-- Gold         | 28
-- Silver       | 17
SELECT loyalty_tier, COUNT(*) FROM customers GROUP BY loyalty_tier;
