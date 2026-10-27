-- Every reject carries a known reason code (expect 0 rows)
SELECT reject_id, source_table, source_key, reason_code
FROM migration_reject
WHERE reason_code IS NULL OR reason_code NOT IN (
  'MISSING_PRICE','PARENT_REJECTED','UNKNOWN_ITEM','UNKNOWN_LOCATION','UNKNOWN_CUSTOMER','INVALID_PERIOD',
  'NEGATIVE_QTY','SUPERSEDED_DUPLICATE','INVALID_LEAD_TIME','INVALID_SS_DAYS','MISSING_EMAIL','DUPLICATE_EMAIL');
