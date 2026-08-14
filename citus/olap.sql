SELECT bid, count(aid), sum(abalance), avg(abalance) 
FROM pgbench_accounts 
GROUP BY bid 
ORDER BY bid;
