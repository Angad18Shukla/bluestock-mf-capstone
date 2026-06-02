"""
data_ingestion.py
Bluestock Fintech — Mutual Fund Analytics Capstone
Day 1: Load all 10 CSV datasets, explore, and validate AMFI codes
"""

from pathlib import Path
import pandas as pd

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).resolve().parent.parent   # project root
RAW_DIR   = BASE_DIR / "data" / "raw"

# ── File map ─────────────────────────────────────────────────────────────────
FILES = {
    "fund_master"          : "01_fund_master.csv",
    "nav_history"          : "02_nav_history.csv",
    "aum_by_fund_house"    : "03_aum_by_fund_house.csv",
    "monthly_sip_inflows"  : "04_monthly_sip_inflows.csv",
    "category_inflows"     : "05_category_inflows.csv",
    "industry_folio_count" : "06_industry_folio_count.csv",
    "scheme_performance"   : "07_scheme_performance.csv",
    "investor_transactions": "08_investor_transactions.csv",
    "portfolio_holdings"   : "09_portfolio_holdings.csv",
    "benchmark_indices"    : "10_benchmark_indices.csv",
}

# ── Helper ────────────────────────────────────────────────────────────────────
def load_and_inspect(name: str, filename: str) -> pd.DataFrame:
    """Load one CSV and print shape / dtypes / head."""
    path = RAW_DIR / filename
    df   = pd.read_csv(path)

    print("=" * 65)
    print(f"  {name}  ({filename})")
    print("=" * 65)
    print(f"  Shape   : {df.shape[0]} rows  x  {df.shape[1]} columns")
    print(f"\n  Columns & dtypes:")
    for col, dtype in df.dtypes.items():
        null_count = df[col].isnull().sum()
        print(f"    {col:<35} {str(dtype):<12}  nulls: {null_count}")
    print(f"\n  First 3 rows:")
    print(df.head(3).to_string(index=False))
    print()
    return df


# ── 1. Load all 10 files ──────────────────────────────────────────────────────
print("\n" + "█" * 65)
print("  STEP 1 — Loading all 10 CSV datasets")
print("█" * 65 + "\n")

dataframes = {}
for name, filename in FILES.items():
    dataframes[name] = load_and_inspect(name, filename)


# ── 2. Explore fund_master ────────────────────────────────────────────────────
print("\n" + "█" * 65)
print("  STEP 2 — Exploring fund_master")
print("█" * 65 + "\n")

fm = dataframes["fund_master"]

print(f"  Unique fund houses ({fm['fund_house'].nunique()}):")
for fh in sorted(fm["fund_house"].unique()):
    print(f"    • {fh}")

print(f"\n  Unique categories ({fm['category'].nunique()}):")
for c in sorted(fm["category"].unique()):
    print(f"    • {c}")

print(f"\n  Unique sub-categories ({fm['sub_category'].nunique()}):")
for sc in sorted(fm["sub_category"].unique()):
    print(f"    • {sc}")

print(f"\n  Unique risk grades ({fm['risk_category'].nunique()}):")
for rg in sorted(fm["risk_category"].unique()):
    print(f"    • {rg}")

print(f"\n  Plan types: {fm['plan'].unique().tolist()}")
print(f"\n  Expense ratio range: "
      f"{fm['expense_ratio_pct'].min():.2f}% — {fm['expense_ratio_pct'].max():.2f}%")


# ── 3. Validate AMFI codes ────────────────────────────────────────────────────
print("\n" + "█" * 65)
print("  STEP 3 — Validating AMFI codes (fund_master vs nav_history)")
print("█" * 65 + "\n")

nav = dataframes["nav_history"]

codes_in_master  = set(fm["amfi_code"].astype(str))
codes_in_nav     = set(nav["amfi_code"].astype(str))

missing_in_nav   = codes_in_master - codes_in_nav
extra_in_nav     = codes_in_nav - codes_in_master

print(f"  Codes in fund_master : {len(codes_in_master)}")
print(f"  Codes in nav_history : {len(codes_in_nav)}")
print(f"  Codes in master but MISSING from nav : {len(missing_in_nav)}")
if missing_in_nav:
    print(f"    {sorted(missing_in_nav)}")
else:
    print("    ✓ None — all master codes exist in nav_history")

print(f"\n  Codes in nav but NOT in master : {len(extra_in_nav)}")
if extra_in_nav:
    print(f"    {sorted(extra_in_nav)}")
else:
    print("    ✓ None — nav_history has no unexpected codes")


# ── 4. Quick data quality summary ────────────────────────────────────────────
print("\n" + "█" * 65)
print("  STEP 4 — Data quality summary across all files")
print("█" * 65 + "\n")

print(f"  {'Dataset':<30} {'Rows':>7}  {'Cols':>5}  {'Total nulls':>12}")
print(f"  {'-'*30} {'-'*7}  {'-'*5}  {'-'*12}")
for name, df in dataframes.items():
    total_nulls = df.isnull().sum().sum()
    print(f"  {name:<30} {df.shape[0]:>7}  {df.shape[1]:>5}  {total_nulls:>12}")

print("\n✅  Day 1 — data_ingestion.py complete!\n")
