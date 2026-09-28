-- Data validation checks. Each check returns ONE number = count of violations (expected 0).
-- Written for SQLite so they run anywhere; MySQL equivalents are noted where the syntax differs.

-- @check V01 | Completeness | Row counts match between source and target
SELECT ABS((SELECT COUNT(*) FROM src_orders) - (SELECT COUNT(*) FROM tgt_orders));

-- @check V02 | Completeness | Source records missing from target
SELECT COUNT(*) FROM src_orders s
LEFT JOIN (SELECT DISTINCT order_id FROM tgt_orders) t ON t.order_id = s.order_id
WHERE t.order_id IS NULL;
-- @detail
SELECT s.order_id, s.customer_id, s.amount FROM src_orders s
LEFT JOIN (SELECT DISTINCT order_id FROM tgt_orders) t ON t.order_id = s.order_id
WHERE t.order_id IS NULL ORDER BY s.order_id;

-- @check V03 | Completeness | Target records with no matching source record
SELECT COUNT(*) FROM tgt_orders t
LEFT JOIN src_orders s ON s.order_id = t.order_id
WHERE s.order_id IS NULL;
-- @detail
SELECT t.order_id, t.customer_id, t.amount FROM tgt_orders t
LEFT JOIN src_orders s ON s.order_id = t.order_id
WHERE s.order_id IS NULL;

-- @check V04 | Nulls | customer_id is NULL in target
SELECT COUNT(*) FROM tgt_orders WHERE customer_id IS NULL;
-- @detail
SELECT order_id, customer_id, amount FROM tgt_orders WHERE customer_id IS NULL;

-- @check V05 | Nulls | amount is NULL in target
SELECT COUNT(*) FROM tgt_orders WHERE amount IS NULL;
-- @detail
SELECT order_id, customer_id, amount FROM tgt_orders WHERE amount IS NULL;

-- @check V06 | Nulls | order_date is NULL in target
SELECT COUNT(*) FROM tgt_orders WHERE order_date IS NULL;

-- @check V07 | Duplicates | Duplicate order_id values in target
SELECT COUNT(*) FROM (SELECT order_id FROM tgt_orders GROUP BY order_id HAVING COUNT(*) > 1);
-- @detail
SELECT order_id, COUNT(*) AS occurrences FROM tgt_orders GROUP BY order_id HAVING COUNT(*) > 1;

-- @check V08 | Data types | amount is not numeric (schema/type error)
-- MySQL: WHERE amount NOT REGEXP '^[0-9]+(\\.[0-9]+)?$'
SELECT COUNT(*) FROM tgt_orders WHERE amount IS NOT NULL AND typeof(amount) NOT IN ('real', 'integer');
-- @detail
SELECT order_id, amount, typeof(amount) AS stored_type FROM tgt_orders
WHERE amount IS NOT NULL AND typeof(amount) NOT IN ('real', 'integer');

-- @check V09 | Data types | order_date not in YYYY-MM-DD format
-- MySQL: WHERE order_date NOT REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
SELECT COUNT(*) FROM tgt_orders
WHERE order_date IS NOT NULL AND order_date NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]';
-- @detail
SELECT order_id, order_date FROM tgt_orders
WHERE order_date IS NOT NULL AND order_date NOT GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]';

-- @check V10 | Validity | status outside allowed values
SELECT COUNT(*) FROM tgt_orders WHERE status NOT IN ('NEW', 'SHIPPED', 'DELIVERED', 'CANCELLED');
-- @detail
SELECT order_id, status FROM tgt_orders WHERE status NOT IN ('NEW', 'SHIPPED', 'DELIVERED', 'CANCELLED');

-- @check V11 | Validity | amount is zero or negative
SELECT COUNT(*) FROM tgt_orders WHERE typeof(amount) IN ('real', 'integer') AND amount <= 0;
