"""
live_nav_fetch.py
Bluestock Fintech — Mutual Fund Analytics Capstone
Day 1: Fetch live historical NAV for 6 schemes from mfapi.in
"""

from pathlib import Path
import requests
import pandas as pd
import time

#  Output folder
BASE_DIR = Path(__file__).resolve().parent.parent   # project root
RAW_DIR  = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

#  Schemes to fetch 
SCHEMES = {
    125497: "HDFC Top 100 Direct",
    119551: "SBI Bluechip Regular",
    120503: "ICICI Pru Bluechip",
    118632: "Nippon India Large Cap",
    119092: "Axis Bluechip",
    120841: "Kotak Bluechip",
}

BASE_URL = "https://api.mfapi.in/mf/{code}"

#  Fetch function 
def fetch_nav(amfi_code: int, scheme_name: str) -> pd.DataFrame | None:
    """
    Call mfapi.in for one scheme code.
    Returns a cleaned DataFrame with columns: amfi_code, scheme_name, date, nav
    """
    url = BASE_URL.format(code=amfi_code)
    print(f"  Fetching {amfi_code} — {scheme_name} ...")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()                  # raise error if HTTP 4xx/5xx
        data = response.json()

        nav_records = data.get("data", [])
        if not nav_records:
            print(f"    ⚠  No data returned for code {amfi_code}")
            return None

        df = pd.DataFrame(nav_records)               # columns: date, nav
        df.rename(columns={"nav": "nav_value"}, inplace=True)

        # Clean types
        df["date"]      = pd.to_datetime(df["date"], format="%d-%m-%Y")
        df["nav_value"] = pd.to_numeric(df["nav_value"], errors="coerce")
        df["amfi_code"] = amfi_code
        df["scheme_name"] = scheme_name

        # Sort oldest → newest
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)

        print(f"    ✓  {len(df)} records  |  "
              f"{df['date'].min().date()} → {df['date'].max().date()}  |  "
              f"Latest NAV: ₹{df['nav_value'].iloc[-1]:.4f}")

        return df[["amfi_code", "scheme_name", "date", "nav_value"]]

    except requests.exceptions.ConnectionError:
        print(f"    ✗  Connection error — check your internet connection.")
        return None
    except requests.exceptions.Timeout:
        print(f"    ✗  Request timed out for code {amfi_code}.")
        return None
    except Exception as e:
        print(f"    ✗  Unexpected error: {e}")
        return None


#  Main 
print("\n" + " " * 65)
print("  STEP 1 — Fetching live NAV from mfapi.in")
print("  API: https://api.mfapi.in/mf/{code}   (no auth required)")
print(" " * 65 + "\n")

all_dfs = []

for code, name in SCHEMES.items():
    df = fetch_nav(code, name)
    if df is not None:
        # Save individual file
        out_file = RAW_DIR / f"nav_live_{code}.csv"
        df.to_csv(out_file, index=False)
        print(f"    💾 Saved → data/raw/nav_live_{code}.csv\n")
        all_dfs.append(df)
    time.sleep(0.5)   # be polite to the free API — small delay between calls


#  Combine all into one file 
if all_dfs:
    combined = pd.concat(all_dfs, ignore_index=True)
    combined_path = RAW_DIR / "nav_live_all_schemes.csv"
    combined.to_csv(combined_path, index=False)

    print("=" * 65)
    print(f"  Combined file saved → data/raw/nav_live_all_schemes.csv")
    print(f"  Total records       : {len(combined)}")
    print(f"  Schemes fetched     : {combined['amfi_code'].nunique()}")
    print(f"\n  Records per scheme:")
    summary = combined.groupby(["amfi_code", "scheme_name"]).size().reset_index(name="records")
    for _, row in summary.iterrows():
        print(f"    {row['amfi_code']}  {row['scheme_name']:<30}  {row['records']} records")
    print("=" * 65)
else:
    print("⚠  No data fetched. Check internet connection and try again.")

print("\n Day 1 — live_nav_fetch.py complete!\n")
