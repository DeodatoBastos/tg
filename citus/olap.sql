SELECT 
    COUNT(aid) as total_processed,
    SUM(LENGTH(REGEXP_REPLACE(REPEAT(MD5(abalance::text), 5), '[a-c]', 'X', 'g'))) as complex_calculation
FROM pgbench_accounts;
