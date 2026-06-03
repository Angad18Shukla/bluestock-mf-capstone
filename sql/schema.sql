-- ============================================================
-- schema.sql
-- Bluestock Fintech — Mutual Fund Analytics Capstone
-- SQLite Star Schema — Day 2
-- ============================================================

-- ── Dimension: Fund master ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code           INTEGER PRIMARY KEY,
    fund_house          TEXT    NOT NULL,
    scheme_name         TEXT    NOT NULL,
    category            TEXT,
    sub_category        TEXT,
    plan                TEXT,
    launch_date         TEXT,
    benchmark           TEXT,
    expense_ratio_pct   REAL,
    exit_load_pct       REAL,
    min_sip_amount      REAL,
    min_lumpsum_amount  REAL,
    fund_manager        TEXT,
    risk_category       TEXT,
    sebi_category_code  TEXT
);

-- ── Dimension: Date ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_date (
    date_id     TEXT    PRIMARY KEY,
    year        INTEGER,
    month       INTEGER,
    quarter     INTEGER,
    month_name  TEXT,
    is_weekday  INTEGER,
    is_monthend INTEGER
);

-- ── Fact: Daily NAV ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER NOT NULL REFERENCES dim_fund(amfi_code),
    date                TEXT    NOT NULL,
    nav                 REAL    NOT NULL,
    daily_return_pct    REAL,
    UNIQUE(amfi_code, date)
);

-- ── Fact: Investor Transactions ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_transactions (
    tx_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id         TEXT,
    transaction_date    TEXT,
    amfi_code           INTEGER REFERENCES dim_fund(amfi_code),
    transaction_type    TEXT,
    amount_inr          REAL,
    state               TEXT,
    city                TEXT,
    city_tier           TEXT,
    age_group           TEXT,
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,
    kyc_status          TEXT
);

-- ── Fact: Scheme Performance ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_performance (
    perf_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER REFERENCES dim_fund(amfi_code),
    scheme_name         TEXT,
    fund_house          TEXT,
    category            TEXT,
    plan                TEXT,
    return_1yr_pct      REAL,
    return_3yr_pct      REAL,
    return_5yr_pct      REAL,
    benchmark_3yr_pct   REAL,
    alpha               REAL,
    beta                REAL,
    sharpe_ratio        REAL,
    sortino_ratio       REAL,
    std_dev_ann_pct     REAL,
    max_drawdown_pct    REAL,
    aum_crore           REAL,
    expense_ratio_pct   REAL,
    morningstar_rating  INTEGER,
    risk_grade          TEXT,
    anomaly_flag        TEXT
);

-- ── Fact: AUM by Fund House ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date            TEXT,
    fund_house      TEXT,
    aum_lakh_crore  REAL,
    aum_crore       REAL,
    num_schemes     INTEGER
);

-- ── Fact: Monthly SIP Industry ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_sip_industry (
    sip_id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    month                       TEXT,
    sip_inflow_crore            REAL,
    active_sip_accounts_crore   REAL,
    new_sip_accounts_lakh       REAL,
    sip_aum_lakh_crore          REAL,
    yoy_growth_pct              REAL
);

-- ── Fact: Portfolio Holdings ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_portfolio (
    holding_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER REFERENCES dim_fund(amfi_code),
    stock_symbol        TEXT,
    stock_name          TEXT,
    sector              TEXT,
    weight_pct          REAL,
    market_value_cr     REAL,
    current_price_inr   REAL,
    portfolio_date      TEXT
);

-- ── Fact: Benchmark Indices ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_benchmark (
    bench_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT,
    index_name  TEXT,
    close_value REAL
);

-- ── Fact: Category Inflows ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_category_inflows (
    inflow_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    month            TEXT,
    category         TEXT,
    net_inflow_crore REAL
);

-- ── Fact: Folio Count ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_folio_count (
    folio_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    month               TEXT,
    total_folios_crore  REAL,
    equity_folios_crore REAL,
    debt_folios_crore   REAL,
    hybrid_folios_crore REAL,
    others_folios_crore REAL
);
