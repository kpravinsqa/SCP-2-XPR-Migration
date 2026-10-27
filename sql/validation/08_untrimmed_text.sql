-- No leading/trailing whitespace in migrated descriptive columns (expect 0 rows)
SELECT 'dim_product' AS tbl, product_id AS k, description AS v FROM dim_product WHERE description <> TRIM(description)
UNION ALL SELECT 'dim_customer', customer_id, customer_name FROM dim_customer WHERE customer_name <> TRIM(customer_name)
UNION ALL SELECT 'dim_site', site_id, site_name FROM dim_site WHERE site_name <> TRIM(site_name)
UNION ALL SELECT 'app_user', username, display_name FROM app_user WHERE display_name <> TRIM(display_name);
