-- MOQ converted from item UOM to eaches (expect 0 rows)
SELECT pp.product_id, pp.site_id, ip.moq, i.case_pack, pp.moq_each
FROM planning_policy pp
JOIN dim_product p     ON p.product_id = pp.product_id
JOIN src.scp_item i    ON i.item_code = p.source_code
JOIN src.scp_item_param ip ON ip.item_code = i.item_code
JOIN dim_site s ON s.site_id = pp.site_id
WHERE ip.loc_code = CASE s.site_id WHEN 'STO' THEN 'STHLM' WHEN 'GOT' THEN 'GBG' WHEN 'OSL' THEN 'OSLO' ELSE s.site_id END
  AND pp.moq_each <> ip.moq * CASE WHEN i.uom = 'CS' THEN i.case_pack ELSE 1 END;
