-- Every source forecast row is either migrated or explicitly rejected (expect 0 rows)
SELECT s.fc_id
FROM src.scp_forecast s
LEFT JOIN fact_demand_forecast f ON f.source_fc_id = s.fc_id
LEFT JOIN migration_reject r     ON r.source_table = 'scp_forecast' AND r.source_key = CAST(s.fc_id AS TEXT)
WHERE f.source_fc_id IS NULL AND r.reject_id IS NULL;
