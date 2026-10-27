-- Product-site-customer-period must be unique in the target (expect 0 rows)
SELECT product_id, site_id, customer_id, period_start, COUNT(*) AS n
FROM fact_demand_forecast
GROUP BY product_id, site_id, customer_id, period_start
HAVING COUNT(*) > 1;
