-- ============================================================
-- queries.sql
-- Bluestock Fintech — Mutual Fund Analytics Capstone
-- 10 Analytical SQL Queries — Day 2
-- Run these in DB Browser for SQLite or via Python sqlite3
-- ============================================================

-- ── Query 1: Top 5 funds by AUM ──────────────────────────────────────────
-- Shows which schemes manage the most money
SELECT
    p.scheme_name,
    p.fund_house,
    p.category,
    p.aum_crore,
    p.sharpe_ratio
FROM fact_performance p
ORDER BY p.aum_crore DESC
LIMIT 5;


-- ── Query 2: Average NAV per month for each fund house ───────────────────
-- Useful for trend analysis across AMCs
SELECT
    strftime('%Y-%m', n.date)   AS month,
    f.fund_house,
    ROUND(AVG(n.nav), 2)        AS avg_nav
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
GROUP BY month, f.fund_house
ORDER BY month, f.fund_house;


-- ── Query 3: SIP inflow YoY growth ───────────────────────────────────────
-- Compare SIP inflows year over year
SELECT
    strftime('%Y', month)           AS year,
    ROUND(SUM(sip_inflow_crore), 0) AS total_sip_crore,
    ROUND(AVG(sip_inflow_crore), 0) AS avg_monthly_sip_crore
FROM fact_sip_industry
GROUP BY year
ORDER BY year;


-- ── Query 4: Total transaction amount by state ───────────────────────────
-- Geographic breakdown of investor activity
SELECT
    state,
    COUNT(*)                            AS num_transactions,
    ROUND(SUM(amount_inr) / 1e7, 2)    AS total_amount_crore,
    ROUND(AVG(amount_inr), 0)           AS avg_transaction_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_crore DESC;


-- ── Query 5: Funds with expense ratio below 1% ───────────────────────────
-- Low-cost funds — better for long-term investors
SELECT
    scheme_name,
    fund_house,
    category,
    plan,
    expense_ratio_pct,
    sharpe_ratio
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;


-- ── Query 6: Best performing funds by 3-year CAGR ────────────────────────
-- Top funds that have beaten their benchmarks
SELECT
    scheme_name,
    fund_house,
    category,
    return_3yr_pct,
    benchmark_3yr_pct,
    ROUND(return_3yr_pct - benchmark_3yr_pct, 2) AS excess_return,
    alpha,
    sharpe_ratio
FROM fact_performance
ORDER BY return_3yr_pct DESC
LIMIT 10;


-- ── Query 7: SIP vs Lumpsum vs Redemption breakdown ──────────────────────
-- Transaction mix analysis
SELECT
    transaction_type,
    COUNT(*)                            AS num_transactions,
    ROUND(SUM(amount_inr) / 1e7, 2)    AS total_amount_crore,
    ROUND(AVG(amount_inr), 0)           AS avg_amount_inr,
    ROUND(COUNT(*) * 100.0 /
        (SELECT COUNT(*) FROM fact_transactions), 1) AS pct_of_total
FROM fact_transactions
GROUP BY transaction_type
ORDER BY num_transactions DESC;


-- ── Query 8: AUM growth by fund house over years ─────────────────────────
-- See which AMCs grew fastest
SELECT
    fund_house,
    strftime('%Y', date)        AS year,
    ROUND(MAX(aum_lakh_crore), 2) AS peak_aum_lakh_crore
FROM fact_aum
GROUP BY fund_house, year
ORDER BY fund_house, year;


-- ── Query 9: Top sectors by portfolio weight across all equity funds ──────
-- What sectors do equity funds collectively own the most?
SELECT
    sector,
    COUNT(DISTINCT amfi_code)           AS num_funds,
    ROUND(AVG(weight_pct), 2)           AS avg_weight_pct,
    ROUND(SUM(market_value_cr), 0)      AS total_market_value_cr
FROM fact_portfolio
GROUP BY sector
ORDER BY total_market_value_cr DESC
LIMIT 10;


-- ── Query 10: Investor demographics — age group vs avg SIP amount ─────────
-- Which age groups invest the most via SIP?
SELECT
    age_group,
    gender,
    COUNT(*)                        AS num_sips,
    ROUND(AVG(amount_inr), 0)       AS avg_sip_amount,
    ROUND(SUM(amount_inr) / 1e7, 2) AS total_amount_crore
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY age_group, gender
ORDER BY age_group, gender;
