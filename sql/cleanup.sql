-- Cleanup / reload steps. The source extract is the system of record, so every defect is repaired from it.
DELETE FROM tgt_orders WHERE rowid NOT IN (SELECT MIN(rowid) FROM tgt_orders GROUP BY order_id);
DELETE FROM tgt_orders WHERE order_id NOT IN (SELECT order_id FROM src_orders);
DELETE FROM tgt_orders WHERE order_id IN (
  SELECT t.order_id FROM tgt_orders t JOIN src_orders s ON s.order_id = t.order_id
  WHERE t.customer_id IS NOT s.customer_id OR t.amount IS NOT s.amount
     OR t.order_date IS NOT s.order_date OR t.status IS NOT s.status);
INSERT INTO tgt_orders SELECT * FROM src_orders WHERE order_id NOT IN (SELECT order_id FROM tgt_orders);
