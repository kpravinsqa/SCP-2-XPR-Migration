-- Every forecast row must reference an existing product, site and customer (expect 0 rows)
SELECT f.forecast_key, f.product_id, f.site_id, f.customer_id
FROM fact_demand_forecast f
LEFT JOIN dim_product  p ON p.product_id  = f.product_id
LEFT JOIN dim_site     s ON s.site_id     = f.site_id
LEFT JOIN dim_customer c ON c.customer_id = f.customer_id
WHERE p.product_id IS NULL OR s.site_id IS NULL OR c.customer_id IS NULL;
