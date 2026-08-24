SELECT 
    COUNT(aid) as num_accounts, 
    SUM(abalance * abalance) as sum_sq, 
    AVG(SQRT(ABS(abalance) + 1)) as avg_sqrt
FROM pgbench_accounts;
