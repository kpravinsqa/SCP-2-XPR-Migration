-- 'YYYYMM' -> 'YYYY-MM-01' (expect 0 rows)
SELECT f.source_fc_id, s.period, f.period_start
FROM fact_demand_forecast f
JOIN src.scp_forecast s ON s.fc_id = f.source_fc_id
WHERE f.period_start <> substr(s.period, 1, 4) || '-' || substr(s.period, 5, 2) || '-01';
