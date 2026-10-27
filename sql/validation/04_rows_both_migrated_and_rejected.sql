-- A source row must not be migrated AND rejected at the same time (expect 0 rows)
SELECT f.source_fc_id
FROM fact_demand_forecast f
JOIN migration_reject r ON r.source_table = 'scp_forecast' AND r.source_key = CAST(f.source_fc_id AS TEXT);
