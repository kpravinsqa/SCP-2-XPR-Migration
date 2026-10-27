-- qty_each = ROUND(fc_qty x pack) where pack = case_pack for CS items, 1 for EA (expect 0 rows)
SELECT f.source_fc_id, s.fc_qty, i.uom, i.case_pack, f.qty_each
FROM fact_demand_forecast f
JOIN src.scp_forecast s ON s.fc_id = f.source_fc_id
JOIN src.scp_item i     ON i.item_code = s.item_code
WHERE f.qty_each <> CAST(ROUND(s.fc_qty * CASE WHEN i.uom = 'CS' THEN i.case_pack ELSE 1 END + 1e-9) AS INTEGER);
