"""
data_cleaning.py
Bluestock Fintech — Mutual Fund Analytics Capstone
Day 2 Task 1-3: Clean nav_history, investor_transactions, scheme_performance
and all remaining CSVs. Save cleaned versions to data/processed/
"""

from pathlib import Path
import pandas as pd
import numpy as np

# - Paths -
BASE_DIR  = Path(__file__).resolve().parent.parent
RAW_DIR   = BASE_DIR / "data" / "raw"
PROC_DIR  = BASE_DIR / "data" / "processed"
PROC_DIR.mkdir(parents=True, exist_ok=True)

def save(df: pd.DataFrame, filename: str):
    path = PROC_DIR / filename
    df.to_csv(path, index=False)
    print(f"  💾 Saved → data/processed/{filename}  ({len(df)} rows)")



# TASK 1 — Clean nav_history.csv
 
print("\n" + " "*65)
print("  TASK 1 — Cleaning nav_history.csv")
print(" "*65)

nav = pd.read_csv(RAW_DIR / "02_nav_history.csv")
print(f"\n  Raw shape : {nav.shape}")

# 1a. Parse date column to datetime
nav["date"] = pd.to_datetime(nav["date"])

# 1b. Ensure nav is numeric, coerce bad values to NaN
nav["nav"] = pd.to_numeric(nav["nav"], errors="coerce")

# 1c. Remove duplicates
before = len(nav)
nav.drop_duplicates(subset=["amfi_code", "date"], inplace=True)
print(f"  Duplicates removed : {before - len(nav)}")

# 1d. Sort by amfi_code then date
nav.sort_values(["amfi_code", "date"], inplace=True)
nav.reset_index(drop=True, inplace=True)

# 1e. Forward-fill missing NAV (weekends / holidays)
#     Reindex each fund to a full calendar date range, then ffill
all_dates = pd.date_range(nav["date"].min(), nav["date"].max(), freq="D")
filled_parts = []
for code, group in nav.groupby("amfi_code"):
    group = group.set_index("date").reindex(all_dates)
    group["amfi_code"] = code
    group["nav"] = group["nav"].ffill()   # forward-fill holidays
    group.index.name = "date"
    group.reset_index(inplace=True)
    filled_parts.append(group)

nav_filled = pd.concat(filled_parts, ignore_index=True)

# 1f. Drop rows where NAV is still NaN (beginning of history before fund launched)
nav_filled.dropna(subset=["nav"], inplace=True)

# 1g. Validate NAV > 0
invalid_nav = nav_filled[nav_filled["nav"] <= 0]
print(f"  Rows with NAV <= 0 : {len(invalid_nav)}")
nav_filled = nav_filled[nav_filled["nav"] > 0]

# 1h. Add daily_return_pct column
nav_filled["daily_return_pct"] = (
    nav_filled.groupby("amfi_code")["nav"]
    .pct_change() * 100
).round(4)

print(f"  Cleaned shape      : {nav_filled.shape}")
print(f"  Date range         : {nav_filled['date'].min().date()} → {nav_filled['date'].max().date()}")
print(f"  Unique schemes     : {nav_filled['amfi_code'].nunique()}")
save(nav_filled, "clean_nav.csv")



# TASK 2 — Clean investor_transactions.csv

print("\n" + " "*65)
print("  TASK 2 — Cleaning investor_transactions.csv")
print(" "*65)

txn = pd.read_csv(RAW_DIR / "08_investor_transactions.csv")
print(f"\n  Raw shape : {txn.shape}")

# 2a. Parse transaction_date
txn["transaction_date"] = pd.to_datetime(txn["transaction_date"])

# 2b. Standardise transaction_type to exactly 3 values
txn["transaction_type"] = txn["transaction_type"].str.strip().str.title()
# Map common variants just in case
type_map = {
    "Sip": "SIP", "Systematic Investment Plan": "SIP",
    "Lump Sum": "Lumpsum", "Lump_Sum": "Lumpsum",
    "Redeem": "Redemption", "Redemption": "Redemption"
}
txn["transaction_type"] = txn["transaction_type"].replace(type_map)
valid_types = ["SIP", "Lumpsum", "Redemption"]
invalid_types = txn[~txn["transaction_type"].isin(valid_types)]
print(f"  Invalid transaction_type rows : {len(invalid_types)}")
txn = txn[txn["transaction_type"].isin(valid_types)]

# 2c. Validate amount > 0
before = len(txn)
txn = txn[txn["amount_inr"] > 0]
print(f"  Rows removed (amount <= 0) : {before - len(txn)}")

# 2d. Check KYC status — keep only Verified / Pending
valid_kyc = ["Verified", "Pending"]
invalid_kyc = txn[~txn["kyc_status"].isin(valid_kyc)]
print(f"  Invalid KYC status rows : {len(invalid_kyc)}")
txn = txn[txn["kyc_status"].isin(valid_kyc)]

# 2e. Remove duplicates
before = len(txn)
txn.drop_duplicates(inplace=True)
print(f"  Duplicates removed : {before - len(txn)}")

# 2f. Summary
print(f"  Cleaned shape : {txn.shape}")
print(f"  Transaction types : {txn['transaction_type'].value_counts().to_dict()}")
print(f"  KYC status counts : {txn['kyc_status'].value_counts().to_dict()}")
save(txn, "clean_transactions.csv")


# TASK 3 — Clean scheme_performance.csv

print("\n" + " "*65)
print("  TASK 3 — Cleaning scheme_performance.csv")
print(" "*65)

perf = pd.read_csv(RAW_DIR / "07_scheme_performance.csv")
print(f"\n  Raw shape : {perf.shape}")

# 3a. Numeric columns — coerce to float
numeric_cols = [
    "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
    "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
    "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct",
    "aum_crore", "expense_ratio_pct"
]
for col in numeric_cols:
    perf[col] = pd.to_numeric(perf[col], errors="coerce")

# 3b. Flag negative Sharpe ratios (anomalies)
neg_sharpe = perf[perf["sharpe_ratio"] < 0]
print(f"  Funds with negative Sharpe : {len(neg_sharpe)}")
if len(neg_sharpe) > 0:
    print(neg_sharpe[["scheme_name", "sharpe_ratio"]])

# 3c. Check expense_ratio range (0.1% – 2.5%)
out_of_range = perf[
    (perf["expense_ratio_pct"] < 0.1) | (perf["expense_ratio_pct"] > 2.5)
]
print(f"  Expense ratio out of range [0.1–2.5%] : {len(out_of_range)}")
if len(out_of_range) > 0:
    print(out_of_range[["scheme_name", "expense_ratio_pct"]])

# 3d. Add a flag column for anomalies
perf["anomaly_flag"] = "OK"
perf.loc[perf["sharpe_ratio"] < 0, "anomaly_flag"] = "NEGATIVE_SHARPE"
perf.loc[
    (perf["expense_ratio_pct"] < 0.1) | (perf["expense_ratio_pct"] > 2.5),
    "anomaly_flag"
] = "EXPENSE_OUT_OF_RANGE"

print(f"  Cleaned shape : {perf.shape}")
print(f"  Expense ratio range : {perf['expense_ratio_pct'].min():.2f}% – {perf['expense_ratio_pct'].max():.2f}%")
save(perf, "clean_performance.csv")



# TASK 4 — Clean remaining 7 CSVs (minimal cleaning needed)

print("\n" + " "*65)
print("  TASK 4 — Cleaning remaining datasets")
print(" "*65 + "\n")

# fund_master
fm = pd.read_csv(RAW_DIR / "01_fund_master.csv")
fm["launch_date"] = pd.to_datetime(fm["launch_date"])
fm["expense_ratio_pct"] = pd.to_numeric(fm["expense_ratio_pct"], errors="coerce")
fm["exit_load_pct"]     = pd.to_numeric(fm["exit_load_pct"],     errors="coerce")
fm.drop_duplicates(subset=["amfi_code"], inplace=True)
save(fm, "clean_fund_master.csv")

# aum_by_fund_house
aum = pd.read_csv(RAW_DIR / "03_aum_by_fund_house.csv")
aum["date"] = pd.to_datetime(aum["date"])
aum["aum_lakh_crore"] = pd.to_numeric(aum["aum_lakh_crore"], errors="coerce")
aum["aum_crore"]      = pd.to_numeric(aum["aum_crore"],      errors="coerce")
save(aum, "clean_aum_by_fund_house.csv")

# monthly_sip_inflows
sip = pd.read_csv(RAW_DIR / "04_monthly_sip_inflows.csv")
sip["month"] = pd.to_datetime(sip["month"], format="%Y-%m")
for col in ["sip_inflow_crore", "active_sip_accounts_crore",
            "new_sip_accounts_lakh", "sip_aum_lakh_crore", "yoy_growth_pct"]:
    sip[col] = pd.to_numeric(sip[col], errors="coerce")
save(sip, "clean_monthly_sip_inflows.csv")

# category_inflows
cat = pd.read_csv(RAW_DIR / "05_category_inflows.csv")
cat["month"] = pd.to_datetime(cat["month"], format="%Y-%m")
cat["net_inflow_crore"] = pd.to_numeric(cat["net_inflow_crore"], errors="coerce")
save(cat, "clean_category_inflows.csv")

# industry_folio_count
folio = pd.read_csv(RAW_DIR / "06_industry_folio_count.csv")
folio["month"] = pd.to_datetime(folio["month"], format="%Y-%m")
save(folio, "clean_industry_folio_count.csv")

# portfolio_holdings
port = pd.read_csv(RAW_DIR / "09_portfolio_holdings.csv")
port["portfolio_date"] = pd.to_datetime(port["portfolio_date"])
port["weight_pct"]     = pd.to_numeric(port["weight_pct"],     errors="coerce")
port["market_value_cr"]= pd.to_numeric(port["market_value_cr"],errors="coerce")
save(port, "clean_portfolio_holdings.csv")

# benchmark_indices
bench = pd.read_csv(RAW_DIR / "10_benchmark_indices.csv")
bench["date"]        = pd.to_datetime(bench["date"])
bench["close_value"] = pd.to_numeric(bench["close_value"], errors="coerce")
bench.sort_values(["index_name", "date"], inplace=True)
bench.reset_index(drop=True, inplace=True)
save(bench, "clean_benchmark_indices.csv")

print("\n  data_cleaning.py complete — all 10 cleaned CSVs in data/processed/\n")
