"""
load_database.py
Bluestock Fintech — Mutual Fund Analytics Capstone
Day 2 Task 4-5: Create SQLite star schema and load all cleaned data
"""

from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

#  Paths 
BASE_DIR = Path(__file__).resolve().parent.parent
PROC_DIR = BASE_DIR / "data" / "processed"
DB_DIR   = BASE_DIR / "data" / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH  = DB_DIR / "bluestock_mf.db"
engine   = create_engine(f"sqlite:///{DB_PATH}", echo=False)



# STEP 1 — Create star schema tables

print("\n" + "█"*65)
print("  STEP 1 — Creating SQLite star schema")
print("█"*65 + "\n")

SCHEMA_SQL = """
-- ── Dimension: Fund master ───────────────────────────────────────────────
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

-- ── Dimension: Date ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_date (
    date_id     TEXT    PRIMARY KEY,
    year        INTEGER,
    month       INTEGER,
    quarter     INTEGER,
    month_name  TEXT,
    is_weekday  INTEGER,
    is_monthend INTEGER
);

-- ── Fact: Daily NAV ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER NOT NULL REFERENCES dim_fund(amfi_code),
    date                TEXT    NOT NULL,
    nav                 REAL    NOT NULL,
    daily_return_pct    REAL,
    UNIQUE(amfi_code, date)
);

-- ── Fact: Investor Transactions ──────────────────────────────────────────
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

-- ── Fact: Scheme Performance ─────────────────────────────────────────────
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

-- ── Fact: AUM by Fund House ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date            TEXT,
    fund_house      TEXT,
    aum_lakh_crore  REAL,
    aum_crore       REAL,
    num_schemes     INTEGER
);

-- ── Fact: Monthly SIP Industry ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_sip_industry (
    sip_id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    month                       TEXT,
    sip_inflow_crore            REAL,
    active_sip_accounts_crore   REAL,
    new_sip_accounts_lakh       REAL,
    sip_aum_lakh_crore          REAL,
    yoy_growth_pct              REAL
);

-- ── Fact: Portfolio Holdings ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_portfolio (
    holding_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code       INTEGER REFERENCES dim_fund(amfi_code),
    stock_symbol    TEXT,
    stock_name      TEXT,
    sector          TEXT,
    weight_pct      REAL,
    market_value_cr REAL,
    current_price_inr REAL,
    portfolio_date  TEXT
);

-- ── Fact: Benchmark Indices ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_benchmark (
    bench_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT,
    index_name  TEXT,
    close_value REAL
);

-- ── Fact: Category Inflows ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_category_inflows (
    inflow_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    month           TEXT,
    category        TEXT,
    net_inflow_crore REAL
);

-- ── Fact: Folio Count ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_folio_count (
    folio_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    month                   TEXT,
    total_folios_crore      REAL,
    equity_folios_crore     REAL,
    debt_folios_crore       REAL,
    hybrid_folios_crore     REAL,
    others_folios_crore     REAL
);
"""

with engine.connect() as conn:
    for statement in SCHEMA_SQL.strip().split(";"):
        statement = statement.strip()
        if statement:
            conn.execute(text(statement))
    conn.commit()

print("  ✓ All tables created successfully")


# ════════════════════════════════════════════════════════════════════════════
# STEP 2 — Build dim_date table (all calendar dates in dataset range)
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "█"*65)
print("  STEP 2 — Building dim_date dimension")
print("█"*65 + "\n")

dates = pd.date_range("2022-01-01", "2026-12-31", freq="D")
dim_date = pd.DataFrame({
    "date_id"    : dates.strftime("%Y-%m-%d"),
    "year"       : dates.year,
    "month"      : dates.month,
    "quarter"    : dates.quarter,
    "month_name" : dates.strftime("%B"),
    "is_weekday" : (dates.weekday < 5).astype(int),
    "is_monthend": dates.is_month_end.astype(int),
})
dim_date.to_sql("dim_date", engine, if_exists="replace", index=False)
print(f"  dim_date loaded : {len(dim_date)} rows")


# ════════════════════════════════════════════════════════════════════════════
# STEP 3 — Load all cleaned CSVs into the database
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "█"*65)
print("  STEP 3 — Loading all cleaned CSVs into SQLite")
print("█"*65 + "\n")

def load_table(csv_file: str, table_name: str, date_cols: list = None):
    """Load one cleaned CSV into a SQLite table."""
    df = pd.read_csv(PROC_DIR / csv_file)
    if date_cols:
        for col in date_cols:
            df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d")
    df.to_sql(table_name, engine, if_exists="replace", index=False)
    print(f"  ✓ {table_name:<30} {len(df):>8} rows  ← {csv_file}")
    return len(df)

load_table("clean_fund_master.csv",          "dim_fund",              ["launch_date"])
load_table("clean_nav.csv",                  "fact_nav",              ["date"])
load_table("clean_transactions.csv",         "fact_transactions",     ["transaction_date"])
load_table("clean_performance.csv",          "fact_performance")
load_table("clean_aum_by_fund_house.csv",    "fact_aum",              ["date"])
load_table("clean_monthly_sip_inflows.csv",  "fact_sip_industry",     ["month"])
load_table("clean_portfolio_holdings.csv",   "fact_portfolio",        ["portfolio_date"])
load_table("clean_benchmark_indices.csv",    "fact_benchmark",        ["date"])
load_table("clean_category_inflows.csv",     "fact_category_inflows", ["month"])
load_table("clean_industry_folio_count.csv", "fact_folio_count",      ["month"])


# ════════════════════════════════════════════════════════════════════════════
# STEP 4 — Verify row counts
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "█"*65)
print("  STEP 4 — Verifying row counts in database")
print("█"*65 + "\n")

tables = [
    "dim_fund", "dim_date", "fact_nav", "fact_transactions",
    "fact_performance", "fact_aum", "fact_sip_industry",
    "fact_portfolio", "fact_benchmark", "fact_category_inflows", "fact_folio_count"
]

with engine.connect() as conn:
    print(f"  {'Table':<35} {'Row count':>10}")
    print(f"  {'-'*35} {'-'*10}")
    for tbl in tables:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {tbl}")).scalar()
        print(f"  {tbl:<35} {count:>10}")

print(f"\n  Database location: {DB_PATH}")
print("\n✅  load_database.py complete!\n")
