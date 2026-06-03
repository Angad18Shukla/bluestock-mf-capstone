# Data Dictionary
## Bluestock Fintech — Mutual Fund Analytics Capstone

**Source datasets:** AMFI India, mfapi.in, NSE/BSE public data  
**Last updated:** June 2026  

---

## Table: dim_fund
**Source file:** 01_fund_master.csv  
**Description:** Master list of 40 real AMFI mutual fund schemes  

| Column | Type | Description |
|--------|------|-------------|
| amfi_code | INTEGER (PK) | Unique AMFI scheme code (e.g. 119551 = SBI Bluechip Regular) |
| fund_house | TEXT | AMC name (e.g. SBI Mutual Fund, HDFC Mutual Fund) |
| scheme_name | TEXT | Full official AMFI scheme name |
| category | TEXT | Broad category: Equity / Debt / Hybrid |
| sub_category | TEXT | SEBI sub-category: Large Cap / Mid Cap / Small Cap / Liquid etc. |
| plan | TEXT | Regular or Direct plan |
| launch_date | TEXT | Fund launch date (YYYY-MM-DD) |
| benchmark | TEXT | Official benchmark index (e.g. NIFTY 100 TRI) |
| expense_ratio_pct | REAL | Annual expense ratio in % (e.g. 1.05 means 1.05%) |
| exit_load_pct | REAL | Exit load percentage (0.0 for liquid/index funds) |
| min_sip_amount | REAL | Minimum SIP amount in ₹ |
| min_lumpsum_amount | REAL | Minimum lumpsum investment in ₹ |
| fund_manager | TEXT | Name of primary fund manager |
| risk_category | TEXT | SEBI risk: Low / Moderate / High / Very High |
| sebi_category_code | TEXT | Internal code: EC01=LargeCap, EC03=SmallCap, DC01=Liquid |

---

## Table: dim_date
**Source:** Generated programmatically  
**Description:** Date dimension covering 2022–2026  

| Column | Type | Description |
|--------|------|-------------|
| date_id | TEXT (PK) | Date in YYYY-MM-DD format |
| year | INTEGER | Calendar year (2022–2026) |
| month | INTEGER | Month number (1–12) |
| quarter | INTEGER | Quarter (1–4) |
| month_name | TEXT | Full month name (e.g. January) |
| is_weekday | INTEGER | 1 = weekday, 0 = Saturday/Sunday |
| is_monthend | INTEGER | 1 = last day of month, 0 = otherwise |

---

## Table: fact_nav
**Source file:** 02_nav_history.csv  
**Description:** Daily NAV for all 40 schemes from Jan 2022 to May 2026  

| Column | Type | Description |
|--------|------|-------------|
| nav_id | INTEGER (PK) | Auto-increment row ID |
| amfi_code | INTEGER (FK) | References dim_fund.amfi_code |
| date | TEXT | NAV date (YYYY-MM-DD), includes forward-filled weekends |
| nav | REAL | Net Asset Value in ₹ on that date |
| daily_return_pct | REAL | Day-over-day return % = (nav_t / nav_t-1 - 1) × 100 |

---

## Table: fact_transactions
**Source file:** 08_investor_transactions.csv  
**Description:** 32,000+ investor transactions — SIP, Lumpsum, Redemption  

| Column | Type | Description |
|--------|------|-------------|
| tx_id | INTEGER (PK) | Auto-increment transaction ID |
| investor_id | TEXT | Unique investor ID (INV000001–INV005000) |
| transaction_date | TEXT | Date of transaction (YYYY-MM-DD) |
| amfi_code | INTEGER (FK) | References dim_fund.amfi_code |
| transaction_type | TEXT | SIP / Lumpsum / Redemption |
| amount_inr | REAL | Transaction amount in Indian Rupees |
| state | TEXT | Investor's home state (12 Indian states) |
| city | TEXT | Investor's city |
| city_tier | TEXT | T30 (Top 30 cities) or B30 (Beyond Top 30) per AMFI |
| age_group | TEXT | 18-25 / 26-35 / 36-45 / 46-55 / 56+ |
| gender | TEXT | Male / Female |
| annual_income_lakh | REAL | Annual income in ₹ lakh |
| payment_mode | TEXT | UPI / Net Banking / Mandate / Cheque |
| kyc_status | TEXT | Verified (92%) / Pending (8%) |

---

## Table: fact_performance
**Source file:** 07_scheme_performance.csv  
**Description:** Risk and return metrics for all 40 schemes  

| Column | Type | Description |
|--------|------|-------------|
| perf_id | INTEGER (PK) | Auto-increment row ID |
| amfi_code | INTEGER (FK) | References dim_fund.amfi_code |
| scheme_name | TEXT | Full scheme name |
| return_1yr_pct | REAL | 1-year absolute return % |
| return_3yr_pct | REAL | 3-year CAGR % |
| return_5yr_pct | REAL | 5-year CAGR % |
| benchmark_3yr_pct | REAL | Benchmark 3-year CAGR for comparison |
| alpha | REAL | Excess return above benchmark (return_3yr - benchmark_3yr) |
| beta | REAL | Market sensitivity — 1.0 = same movement as market |
| sharpe_ratio | REAL | Risk-adjusted return — higher is better, >1 is good |
| sortino_ratio | REAL | Like Sharpe but only penalises downside volatility |
| std_dev_ann_pct | REAL | Annualised standard deviation of daily returns % |
| max_drawdown_pct | REAL | Worst peak-to-trough decline (negative value, e.g. -21.7) |
| aum_crore | REAL | Scheme AUM in ₹ crore (NOT lakh crore) |
| expense_ratio_pct | REAL | Annual expense ratio % |
| morningstar_rating | INTEGER | 1–5 star rating based on Sharpe ratio |
| risk_grade | TEXT | Low / Moderate / High / Very High |
| anomaly_flag | TEXT | OK / NEGATIVE_SHARPE / EXPENSE_OUT_OF_RANGE |

---

## Table: fact_aum
**Source file:** 03_aum_by_fund_house.csv  
**Description:** Quarterly AUM for 10 fund houses, 2022–2025  

| Column | Type | Description |
|--------|------|-------------|
| aum_id | INTEGER (PK) | Auto-increment row ID |
| date | TEXT | Quarter end date (YYYY-MM-DD) |
| fund_house | TEXT | AMC name |
| aum_lakh_crore | REAL | AUM in ₹ lakh crore (e.g. 12.5 = ₹12.5 lakh crore) |
| aum_crore | REAL | Same AUM in ₹ crore (aum_lakh_crore × 100,000) |
| num_schemes | INTEGER | Number of schemes managed by this AMC |

---

## Table: fact_sip_industry
**Source file:** 04_monthly_sip_inflows.csv  
**Description:** Industry-wide monthly SIP data Jan 2022–Dec 2025  

| Column | Type | Description |
|--------|------|-------------|
| sip_id | INTEGER (PK) | Auto-increment row ID |
| month | TEXT | Month (YYYY-MM-DD, first day of month) |
| sip_inflow_crore | REAL | Total SIP inflows that month in ₹ crore |
| active_sip_accounts_crore | REAL | Active SIP accounts in crore |
| new_sip_accounts_lakh | REAL | New SIP registrations that month in lakh |
| sip_aum_lakh_crore | REAL | Total SIP AUM in ₹ lakh crore |
| yoy_growth_pct | REAL | Year-over-year growth % in SIP inflows |

---

## Table: fact_portfolio
**Source file:** 09_portfolio_holdings.csv  
**Description:** Top stock holdings per equity fund as of Dec 2025  

| Column | Type | Description |
|--------|------|-------------|
| holding_id | INTEGER (PK) | Auto-increment row ID |
| amfi_code | INTEGER (FK) | References dim_fund.amfi_code |
| stock_symbol | TEXT | NSE/BSE ticker (e.g. HDFCBANK) |
| stock_name | TEXT | Full company name |
| sector | TEXT | Sector (Banking, IT, FMCG etc.) |
| weight_pct | REAL | Portfolio weight % for this stock in this fund |
| market_value_cr | REAL | Market value of holding in ₹ crore |
| current_price_inr | REAL | Stock price in ₹ as of portfolio_date |
| portfolio_date | TEXT | Date of portfolio disclosure (YYYY-MM-DD) |

---

## Table: fact_benchmark
**Source file:** 10_benchmark_indices.csv  
**Description:** Daily closing values for 7 major indices  

| Column | Type | Description |
|--------|------|-------------|
| bench_id | INTEGER (PK) | Auto-increment row ID |
| date | TEXT | Trading date (YYYY-MM-DD) |
| index_name | TEXT | NIFTY50 / NIFTY100 / NIFTY_MIDCAP150 / BSE_SMALLCAP / NIFTY500 / CRISIL_LIQUID / CRISIL_GILT |
| close_value | REAL | Index closing value on that date |

---

## Table: fact_category_inflows
**Source file:** 05_category_inflows.csv  
**Description:** Net inflows by fund category for FY 2024–25  

| Column | Type | Description |
|--------|------|-------------|
| inflow_id | INTEGER (PK) | Auto-increment row ID |
| month | TEXT | Month (YYYY-MM-DD) |
| category | TEXT | Fund category (Large Cap, Mid Cap, Small Cap, ELSS, Liquid etc.) |
| net_inflow_crore | REAL | Net inflow (positive = net buy, negative = net redemption) in ₹ crore |

---

## Table: fact_folio_count
**Source file:** 06_industry_folio_count.csv  
**Description:** Total MF folios growth from Jan 2022 to Dec 2025  

| Column | Type | Description |
|--------|------|-------------|
| folio_id | INTEGER (PK) | Auto-increment row ID |
| month | TEXT | Month (YYYY-MM-DD) |
| total_folios_crore | REAL | Total MF folios in crore (13.26 Cr Jan 2022 → 26.12 Cr Dec 2025) |
| equity_folios_crore | REAL | Equity fund folios in crore |
| debt_folios_crore | REAL | Debt fund folios in crore |
| hybrid_folios_crore | REAL | Hybrid fund folios in crore |
| others_folios_crore | REAL | Other category folios in crore |

---

## Key business metrics reference

| Metric | Value | Source |
|--------|-------|--------|
| Industry AUM Dec 2025 | ₹81 lakh crore | AMFI |
| SBI MF AUM Dec 2025 | ₹12.50 lakh crore | AMFI Quarterly |
| SIP Inflow Dec 2025 | ₹31,002 crore (all-time high) | AMFI Monthly Note |
| Active SIP Accounts Dec 2025 | 9.35 crore | AMFI |
| Total MF Folios Dec 2025 | 26.12 crore | AMFI |
| Total schemes covered | 40 | This project |
| Total transactions | 32,778 | Simulated from real distributions |