-- product_id = UPPER(item_code) without spaces and dashes; lineage column preserved (expect 0 rows)
SELECT p.product_id, p.source_code
FROM dim_product p
WHERE p.product_id <> UPPER(REPLACE(REPLACE(p.source_code, '-', ''), ' ', ''))
   OR p.source_code NOT IN (SELECT item_code FROM src.scp_item);
