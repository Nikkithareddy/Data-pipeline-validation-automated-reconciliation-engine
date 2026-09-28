-- Reconciliation checks: aggregates and joins compared against the source extract.

-- @check R01 | Reconciliation | Total amount differs between source and target
SELECT ROUND(ABS(
  (SELECT SUM(amount) FROM src_orders) -
  (SELECT SUM(amount) FROM tgt_orders WHERE typeof(amount) IN ('real','integer'))
), 2);

-- @check R02 | Reconciliation | Row-level amount mismatches (joined on order_id)
SELECT COUNT(*) FROM src_orders s
JOIN tgt_orders t ON t.order_id = s.order_id
WHERE t.amount IS NOT NULL AND s.amount <> t.amount;
-- @detail
SELECT s.order_id, s.amount AS source_amount, t.amount AS target_amount FROM src_orders s
JOIN tgt_orders t ON t.order_id = s.order_id
WHERE t.amount IS NOT NULL AND s.amount <> t.amount ORDER BY s.order_id;

-- @check R03 | Reconciliation | Customers whose order totals differ from source
SELECT COUNT(*) FROM (
  SELECT customer_id, ROUND(SUM(amount), 2) AS total FROM src_orders GROUP BY customer_id
) s
LEFT JOIN (
  SELECT customer_id, ROUND(SUM(amount), 2) AS total FROM tgt_orders
  WHERE typeof(amount) IN ('real','integer') GROUP BY customer_id
) t ON t.customer_id = s.customer_id
WHERE t.total IS NULL OR t.total <> s.total;
-- @detail
SELECT s.customer_id, s.total AS source_total, t.total AS target_total FROM (
  SELECT customer_id, ROUND(SUM(amount), 2) AS total FROM src_orders GROUP BY customer_id
) s
LEFT JOIN (
  SELECT customer_id, ROUND(SUM(amount), 2) AS total FROM tgt_orders
  WHERE typeof(amount) IN ('real','integer') GROUP BY customer_id
) t ON t.customer_id = s.customer_id
WHERE t.total IS NULL OR t.total <> s.total ORDER BY s.customer_id;

-- @check R04 | Reconciliation | Status buckets whose counts differ from source
SELECT COUNT(*) FROM (
  SELECT status, COUNT(*) AS n FROM src_orders GROUP BY status
) s
LEFT JOIN (
  SELECT status, COUNT(*) AS n FROM tgt_orders GROUP BY status
) t ON t.status = s.status
WHERE t.n IS NULL OR t.n <> s.n;
