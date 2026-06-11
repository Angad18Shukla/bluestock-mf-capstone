"""
performance_analytics.py
========================
Day 4 — Fund Performance Analytics
Bluestock Fintech Capstone Project

HOW TO RUN:
    From your project root  (bluestock_mf_capstone/):
        python scripts/performance_analytics.py

WHAT IT PRODUCES  (all saved to data/processed/ and reports/):
    returns_computed.csv      — daily returns for all 40 funds
    cagr_report.csv           — 1yr / 3yr / 5yr CAGR per fund
    sharpe_values.csv         — Sharpe ratio ranked
    sortino_values.csv        — Sortino ratio ranked
    alpha_beta.csv            — OLS Alpha & Beta vs NIFTY100
    max_drawdown.csv          — max drawdown + worst period dates
    fund_scorecard.csv        — composite 0-100 score, final ranking
    benchmark_chart.png       — top-5 funds vs NIFTY50 + NIFTY100
"""

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")                  # non-interactive backend — works everywhere
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats

warnings.filterwarnings("ignore")

# Paths 
ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW       = os.path.join(ROOT, "data", "raw")
PROCESSED = os.path.join(ROOT, "data", "processed")
REPORTS   = os.path.join(ROOT, "reports")
os.makedirs(PROCESSED, exist_ok=True)
os.makedirs(REPORTS,   exist_ok=True)

#  Constants 
RF_ANNUAL   = 0.065          # Risk-free rate: 6.5% (RBI repo rate proxy)
RF_DAILY    = RF_ANNUAL / 252
TRADING_DAYS = 252



# SECTION 0 — Load & prepare data

def load_data():
    print("\n" + "═"*65)
    print("  LOADING DATA")
    print("═"*65)

    nav = pd.read_csv(os.path.join(RAW, "02_nav_history.csv"))
    nav["date"] = pd.to_datetime(nav["date"])
    nav = nav.sort_values(["amfi_code", "date"]).reset_index(drop=True)

    fm = pd.read_csv(os.path.join(RAW, "01_fund_master.csv"))

    bi = pd.read_csv(os.path.join(RAW, "10_benchmark_indices.csv"))
    bi["date"] = pd.to_datetime(bi["date"])

    print(f"  NAV history   : {len(nav):,} rows | {nav['amfi_code'].nunique()} funds")
    print(f"  Fund master   : {len(fm)} funds")
    print(f"  Benchmarks    : {sorted(bi['index_name'].unique())}")
    print(f"  Date range    : {nav['date'].min().date()} → {nav['date'].max().date()}")

    return nav, fm, bi



# TASK 1 — Daily Returns

def compute_daily_returns(nav: pd.DataFrame) -> pd.DataFrame:
    """
    daily_return = (nav_t / nav_t-1) - 1
    Computed per fund using groupby + pct_change.
    First row per fund is NaN (no prior day) — we drop it.
    """
    print("\n" + "─"*65)
    print("  TASK 1 — Computing Daily Returns")
    print("─"*65)

    nav = nav.sort_values(["amfi_code", "date"])

    # pct_change() = (current - previous) / previous  = nav_t/nav_t-1 - 1
    nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()

    # Drop the NaN first-row per fund
    returns = nav.dropna(subset=["daily_return"]).copy()

    # ── Validation ────────────────────────────────────────────────────────────
    print(f"  Rows after dropping NaN first-rows : {len(returns):,}")
    print(f"  Return distribution (all funds combined):")
    desc = returns["daily_return"].describe()
    print(f"    Mean   : {desc['mean']*100:.4f}%")
    print(f"    Std    : {desc['std']*100:.4f}%")
    print(f"    Min    : {desc['min']*100:.4f}%  (worst single day)")
    print(f"    Max    : {desc['max']*100:.4f}%  (best single day)")
    print(f"    25th % : {desc['25%']*100:.4f}%")
    print(f"    75th % : {desc['75%']*100:.4f}%")

    # Sanity check — no return should be > 50% or < -50% in a day
    extreme = returns[returns["daily_return"].abs() > 0.5]
    if len(extreme) == 0:
        print(f"    No extreme daily returns (>50%) found — distribution looks reasonable")
    else:
        print(f"     {len(extreme)} extreme returns found — investigate:")
        print(extreme[["amfi_code","date","nav","daily_return"]].to_string())

    out_path = os.path.join(PROCESSED, "returns_computed.csv")
    returns.to_csv(out_path, index=False)
    print(f"    Saved: returns_computed.csv  ({len(returns):,} rows)")

    return returns


# ══════════════════════════════════════════════════════════════════════════════
# TASK 2 — CAGR (1yr, 3yr, 5yr)
# ══════════════════════════════════════════════════════════════════════════════
def compute_cagr(nav: pd.DataFrame, fm: pd.DataFrame) -> pd.DataFrame:
    """
    CAGR formula:
        CAGR = (NAV_end / NAV_start) ^ (1/n) - 1
    where n = number of years.

    We use actual NAV values at the start and end of each window.
    If data doesn't cover the full window, we return NaN for that period.
    """
    print("\n" + "─"*65)
    print("  TASK 2 — Computing CAGR (1yr, 3yr, 5yr)")
    print("─"*65)

    latest_date = nav["date"].max()
    date_1yr    = latest_date - pd.DateOffset(years=1)
    date_3yr    = latest_date - pd.DateOffset(years=3)
    date_5yr    = latest_date - pd.DateOffset(years=5)
    oldest_date = nav["date"].min()

    print(f"  Latest date  : {latest_date.date()}")
    print(f"  1yr start    : {date_1yr.date()}")
    print(f"  3yr start    : {date_3yr.date()}")
    print(f"  5yr start    : {date_5yr.date()}  ← data starts {oldest_date.date()}, so 5yr may be NaN")

    def get_nav_on_or_after(code_nav: pd.DataFrame, target_date) -> float:
        """Get NAV on target_date or the nearest trading day after it."""
        subset = code_nav[code_nav["date"] >= target_date]
        if subset.empty:
            return np.nan
        return subset.iloc[0]["nav"]

    records = []
    for code, grp in nav.groupby("amfi_code"):
        grp = grp.sort_values("date")

        nav_end = grp.iloc[-1]["nav"]          # latest available NAV

        # ── 1yr CAGR ──────────────────────────────────────────────────────────
        nav_start_1yr = get_nav_on_or_after(grp, date_1yr)
        cagr_1yr = (nav_end / nav_start_1yr) ** (1 / 1) - 1 if not np.isnan(nav_start_1yr) else np.nan

        # ── 3yr CAGR ──────────────────────────────────────────────────────────
        nav_start_3yr = get_nav_on_or_after(grp, date_3yr)
        cagr_3yr = (nav_end / nav_start_3yr) ** (1 / 3) - 1 if not np.isnan(nav_start_3yr) else np.nan

        # ── 5yr CAGR — only if data goes back far enough ─────────────────────
        nav_start_5yr = get_nav_on_or_after(grp, date_5yr)
        if not np.isnan(nav_start_5yr) and grp["date"].min() <= date_5yr:
            cagr_5yr = (nav_end / nav_start_5yr) ** (1 / 5) - 1
        else:
            cagr_5yr = np.nan    # data starts Jan 2022, 5yr not available for most

        # ── Available period CAGR (full dataset window) ───────────────────────
        nav_start_full = grp.iloc[0]["nav"]
        n_years = (grp.iloc[-1]["date"] - grp.iloc[0]["date"]).days / 365.25
        cagr_full = (nav_end / nav_start_full) ** (1 / n_years) - 1 if n_years > 0 else np.nan

        records.append({
            "amfi_code"          : code,
            "nav_latest"         : round(nav_end, 4),
            "cagr_1yr_pct"       : round(cagr_1yr * 100, 2) if not np.isnan(cagr_1yr) else np.nan,
            "cagr_3yr_pct"       : round(cagr_3yr * 100, 2) if not np.isnan(cagr_3yr) else np.nan,
            "cagr_5yr_pct"       : round(cagr_5yr * 100, 2) if not np.isnan(cagr_5yr) else np.nan,
            "cagr_full_period_pct": round(cagr_full * 100, 2),
            "data_years"         : round(n_years, 2),
        })

    cagr_df = pd.DataFrame(records)

    # Merge scheme names for readability
    cagr_df = cagr_df.merge(
        fm[["amfi_code", "scheme_name", "fund_house", "sub_category", "plan"]],
        on="amfi_code", how="left"
    )

    # Sort by 3yr CAGR descending
    cagr_df = cagr_df.sort_values("cagr_3yr_pct", ascending=False).reset_index(drop=True)

    # ── Print comparison table ─────────────────────────────────────────────────
    print(f"\n  CAGR Comparison Table (sorted by 3yr CAGR):")
    print(f"  {'Fund':<45} {'1yr%':>7} {'3yr%':>7} {'Full%':>7}")
    print(f"  {'─'*45} {'─'*7} {'─'*7} {'─'*7}")
    for _, row in cagr_df.iterrows():
        name  = str(row["scheme_name"])[:44]
        c1    = f"{row['cagr_1yr_pct']:.1f}" if pd.notna(row["cagr_1yr_pct"]) else " N/A"
        c3    = f"{row['cagr_3yr_pct']:.1f}" if pd.notna(row["cagr_3yr_pct"]) else " N/A"
        cfull = f"{row['cagr_full_period_pct']:.1f}"
        print(f"  {name:<45} {c1:>7} {c3:>7} {cfull:>7}")

    out_path = os.path.join(PROCESSED, "cagr_report.csv")
    cagr_df.to_csv(out_path, index=False)
    print(f"\n   Saved: cagr_report.csv")
    print(f"  Note: 5yr CAGR is NaN — dataset starts Jan 2022 (only ~4.4 yrs available)")

    return cagr_df


# ══════════════════════════════════════════════════════════════════════════════
# TASK 3 — Sharpe Ratio
# ══════════════════════════════════════════════════════════════════════════════
def compute_sharpe(returns: pd.DataFrame, fm: pd.DataFrame) -> pd.DataFrame:
    """
    Sharpe Ratio = (Rp - Rf) / Std(Rp)  ×  √252

    Where:
        Rp  = mean daily return of the fund
        Rf  = daily risk-free rate = 6.5% / 252
        Std = standard deviation of daily returns
        √252 = annualisation factor

    Higher Sharpe = better risk-adjusted return.
    Sharpe > 1.0 is generally considered good.
    """
    print("\n" + "─"*65)
    print("  TASK 3 — Sharpe Ratio")
    print("─"*65)

    records = []
    for code, grp in returns.groupby("amfi_code"):
        r = grp["daily_return"].dropna()
        if len(r) < 30:
            continue

        mean_r = r.mean()
        std_r  = r.std()

        sharpe = (mean_r - RF_DAILY) / std_r * np.sqrt(TRADING_DAYS) if std_r > 0 else np.nan

        records.append({
            "amfi_code"         : code,
            "mean_daily_ret"    : round(mean_r * 100, 5),
            "std_daily_ret"     : round(std_r * 100, 5),
            "sharpe_ratio"      : round(sharpe, 4),
            "annualised_ret_pct": round(((1 + mean_r) ** TRADING_DAYS - 1) * 100, 2),
            "n_days"            : len(r),
        })

    sharpe_df = pd.DataFrame(records)
    sharpe_df = sharpe_df.merge(
        fm[["amfi_code", "scheme_name", "fund_house", "sub_category", "plan"]],
        on="amfi_code", how="left"
    )

    # Rank: highest Sharpe = rank 1
    sharpe_df["sharpe_rank"] = sharpe_df["sharpe_ratio"].rank(ascending=False).astype(int)
    sharpe_df = sharpe_df.sort_values("sharpe_rank")

    print(f"\n  TOP 10 FUNDS BY SHARPE RATIO:")
    print(f"  {'Rank':<6} {'Fund':<45} {'Sharpe':>8} {'Ann.Ret%':>9}")
    print(f"  {'─'*6} {'─'*45} {'─'*8} {'─'*9}")
    for _, row in sharpe_df.head(10).iterrows():
        print(f"  {int(row['sharpe_rank']):<6} {str(row['scheme_name'])[:44]:<45} {row['sharpe_ratio']:>8.4f} {row['annualised_ret_pct']:>8.2f}%")

    out_path = os.path.join(PROCESSED, "sharpe_values.csv")
    sharpe_df.to_csv(out_path, index=False)
    print(f"\n   Saved: sharpe_values.csv")

    return sharpe_df


# ══════════════════════════════════════════════════════════════════════════════
# TASK 4 — Sortino Ratio
# ══════════════════════════════════════════════════════════════════════════════
def compute_sortino(returns: pd.DataFrame, fm: pd.DataFrame) -> pd.DataFrame:
    """
    Sortino Ratio = (Rp - Rf) / Downside_Std  ×  √252

    Downside_Std = std of ONLY the negative return days.

    Why Sortino over Sharpe?
        Sharpe penalises both upside and downside volatility equally.
        Sortino only penalises harmful (negative) volatility.
        A fund with big upward swings but small downward swings
        will have a BETTER Sortino than Sharpe — which is more fair.
    """
    print("\n" + "─"*65)
    print("  TASK 4 — Sortino Ratio")
    print("─"*65)

    records = []
    for code, grp in returns.groupby("amfi_code"):
        r = grp["daily_return"].dropna()
        if len(r) < 30:
            continue

        mean_r        = r.mean()
        downside_r    = r[r < 0]                          # only negative return days
        downside_std  = downside_r.std() if len(downside_r) > 1 else np.nan

        sortino = (mean_r - RF_DAILY) / downside_std * np.sqrt(TRADING_DAYS) \
                  if (downside_std is not np.nan and downside_std > 0) else np.nan

        records.append({
            "amfi_code"          : code,
            "sortino_ratio"      : round(sortino, 4),
            "downside_std_daily" : round(downside_std * 100, 5) if not np.isnan(downside_std) else np.nan,
            "neg_return_days"    : len(downside_r),
            "total_days"         : len(r),
            "pct_negative_days"  : round(len(downside_r) / len(r) * 100, 2),
        })

    sortino_df = pd.DataFrame(records)
    sortino_df = sortino_df.merge(
        fm[["amfi_code", "scheme_name", "fund_house", "sub_category", "plan"]],
        on="amfi_code", how="left"
    )

    sortino_df["sortino_rank"] = sortino_df["sortino_ratio"].rank(ascending=False).astype(int)
    sortino_df = sortino_df.sort_values("sortino_rank")

    print(f"\n  TOP 10 FUNDS BY SORTINO RATIO:")
    print(f"  {'Rank':<6} {'Fund':<45} {'Sortino':>8} {'Neg Days%':>10}")
    print(f"  {'─'*6} {'─'*45} {'─'*8} {'─'*10}")
    for _, row in sortino_df.head(10).iterrows():
        print(f"  {int(row['sortino_rank']):<6} {str(row['scheme_name'])[:44]:<45} {row['sortino_ratio']:>8.4f} {row['pct_negative_days']:>9.1f}%")

    out_path = os.path.join(PROCESSED, "sortino_values.csv")
    sortino_df.to_csv(out_path, index=False)
    print(f"\n    Saved: sortino_values.csv")

    return sortino_df


# ══════════════════════════════════════════════════════════════════════════════
# TASK 5 — Alpha & Beta (OLS Regression vs NIFTY100)
# ══════════════════════════════════════════════════════════════════════════════
def compute_alpha_beta(returns: pd.DataFrame, bi: pd.DataFrame, fm: pd.DataFrame) -> pd.DataFrame:
    """
    OLS Regression:
        fund_return = Alpha + Beta × benchmark_return + error

    scipy.stats.linregress gives:
        slope     = Beta  (sensitivity to market)
        intercept = daily Alpha → annualise: Alpha = intercept × 252

    Interpretation:
        Beta  > 1.0  → fund moves MORE than the market (aggressive)
        Beta  < 1.0  → fund moves LESS than the market (defensive)
        Alpha > 0    → fund generates excess return above what Beta explains
        Alpha < 0    → fund underperforms its risk-adjusted benchmark
    """
    print("\n" + "─"*65)
    print("  TASK 5 — Alpha & Beta (OLS vs NIFTY100)")
    print("─"*65)

    # Prepare benchmark daily returns
    n100 = bi[bi["index_name"] == "NIFTY100"].copy()
    n100 = n100.sort_values("date").reset_index(drop=True)
    n100["bm_return"] = n100["close_value"].pct_change()
    n100 = n100.dropna(subset=["bm_return"])

    records = []
    for code, grp in returns.groupby("amfi_code"):
        grp = grp.sort_values("date")

        # Merge fund returns with benchmark on matching dates
        merged = grp[["date", "daily_return"]].merge(
            n100[["date", "bm_return"]], on="date", how="inner"
        ).dropna()

        if len(merged) < 60:        # need at least 60 trading days for reliable regression
            print(f"     {code}: only {len(merged)} matching days — skipping")
            continue

        x = merged["bm_return"].values
        y = merged["daily_return"].values

        # OLS regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        beta         = slope
        alpha_daily  = intercept
        alpha_annual = intercept * TRADING_DAYS    # annualise
        r_squared    = r_value ** 2

        # Tracking error = std of (fund_return - benchmark_return) × √252
        diff = merged["daily_return"] - merged["bm_return"]
        tracking_error = diff.std() * np.sqrt(TRADING_DAYS) * 100

        records.append({
            "amfi_code"          : code,
            "alpha_annual_pct"   : round(alpha_annual * 100, 4),
            "beta"               : round(beta, 4),
            "r_squared"          : round(r_squared, 4),
            "p_value_beta"       : round(p_value, 6),
            "tracking_error_pct" : round(tracking_error, 4),
            "n_matched_days"     : len(merged),
        })

    alpha_beta_df = pd.DataFrame(records)
    alpha_beta_df = alpha_beta_df.merge(
        fm[["amfi_code", "scheme_name", "fund_house", "sub_category", "plan"]],
        on="amfi_code", how="left"
    )

    alpha_beta_df["alpha_rank"] = alpha_beta_df["alpha_annual_pct"].rank(ascending=False).astype(int)
    alpha_beta_df = alpha_beta_df.sort_values("alpha_rank")

    print(f"\n  TOP 10 FUNDS BY ALPHA (vs NIFTY100):")
    print(f"  {'Rank':<6} {'Fund':<45} {'Alpha%':>8} {'Beta':>6} {'R²':>6}")
    print(f"  {'─'*6} {'─'*45} {'─'*8} {'─'*6} {'─'*6}")
    for _, row in alpha_beta_df.head(10).iterrows():
        print(f"  {int(row['alpha_rank']):<6} {str(row['scheme_name'])[:44]:<45} "
              f"{row['alpha_annual_pct']:>7.2f}% {row['beta']:>6.3f} {row['r_squared']:>6.3f}")

    # Print beta range summary
    print(f"\n  Beta summary:")
    print(f"    < 0.8 (defensive) : {(alpha_beta_df['beta'] < 0.8).sum()} funds")
    print(f"    0.8–1.0 (moderate): {((alpha_beta_df['beta'] >= 0.8) & (alpha_beta_df['beta'] <= 1.0)).sum()} funds")
    print(f"    > 1.0 (aggressive): {(alpha_beta_df['beta'] > 1.0).sum()} funds")

    out_path = os.path.join(PROCESSED, "alpha_beta.csv")
    alpha_beta_df.to_csv(out_path, index=False)
    print(f"\n   Saved: alpha_beta.csv")

    return alpha_beta_df


# ══════════════════════════════════════════════════════════════════════════════
# TASK 6 — Maximum Drawdown
# ══════════════════════════════════════════════════════════════════════════════
def compute_max_drawdown(nav: pd.DataFrame, fm: pd.DataFrame) -> pd.DataFrame:
    """
    Maximum Drawdown = min(NAV / running_max - 1)

    Steps per fund:
        1. Compute running maximum NAV up to each date
        2. Compute drawdown = (NAV - running_max) / running_max
        3. Max drawdown = the minimum drawdown value (most negative)
        4. Find start date (peak) and end date (trough) of worst drawdown
        5. Find recovery date (when NAV gets back above the peak)
    """
    print("\n" + "─"*65)
    print("  TASK 6 — Maximum Drawdown")
    print("─"*65)

    records = []
    for code, grp in nav.groupby("amfi_code"):
        grp = grp.sort_values("date").reset_index(drop=True)

        # Running max up to each date
        grp["running_max"] = grp["nav"].cummax()

        # Drawdown at each point
        grp["drawdown"] = grp["nav"] / grp["running_max"] - 1

        # Maximum drawdown value (most negative)
        max_dd = grp["drawdown"].min()

        # Trough date — where max drawdown occurred
        trough_idx  = grp["drawdown"].idxmin()
        trough_date = grp.loc[trough_idx, "date"]
        trough_nav  = grp.loc[trough_idx, "nav"]

        # Peak date — last time NAV was at running max before the trough
        peak_nav  = grp.loc[trough_idx, "running_max"]
        peak_rows = grp[(grp["nav"] >= peak_nav) & (grp["date"] <= trough_date)]
        peak_date = peak_rows.iloc[-1]["date"] if not peak_rows.empty else grp.iloc[0]["date"]

        # Recovery date — first date after trough where NAV exceeds peak
        recovery_rows = grp[(grp["date"] > trough_date) & (grp["nav"] >= peak_nav)]
        recovery_date = recovery_rows.iloc[0]["date"] if not recovery_rows.empty else None

        # Duration: peak → trough in trading days
        dd_duration = ((trough_date - peak_date).days)

        records.append({
            "amfi_code"          : code,
            "max_drawdown_pct"   : round(max_dd * 100, 4),
            "peak_date"          : peak_date.date(),
            "trough_date"        : trough_date.date(),
            "peak_nav"           : round(peak_nav, 4),
            "trough_nav"         : round(trough_nav, 4),
            "drawdown_duration_days": dd_duration,
            "recovered"          : recovery_date is not None,
            "recovery_date"      : recovery_date.date() if recovery_date else "Not yet",
        })

    dd_df = pd.DataFrame(records)
    dd_df = dd_df.merge(
        fm[["amfi_code", "scheme_name", "fund_house", "sub_category", "plan"]],
        on="amfi_code", how="left"
    )

    dd_df["dd_rank"] = dd_df["max_drawdown_pct"].rank(ascending=False).astype(int)  # least bad = rank 1
    dd_df = dd_df.sort_values("max_drawdown_pct", ascending=False)

    print(f"\n  DRAWDOWN TABLE (best → worst):")
    print(f"  {'Fund':<45} {'MaxDD%':>8} {'Peak':>12} {'Trough':>12} {'Days':>6}")
    print(f"  {'─'*45} {'─'*8} {'─'*12} {'─'*12} {'─'*6}")
    for _, row in dd_df.iterrows():
        print(f"  {str(row['scheme_name'])[:44]:<45} "
              f"{row['max_drawdown_pct']:>7.2f}% "
              f"{str(row['peak_date']):>12} "
              f"{str(row['trough_date']):>12} "
              f"{row['drawdown_duration_days']:>6}")

    out_path = os.path.join(PROCESSED, "max_drawdown.csv")
    dd_df.to_csv(out_path, index=False)
    print(f"\n    Saved: max_drawdown.csv")

    return dd_df


# ══════════════════════════════════════════════════════════════════════════════
# TASK 7 — Fund Scorecard (0–100 composite score)
# ══════════════════════════════════════════════════════════════════════════════
def build_fund_scorecard(cagr_df, sharpe_df, alpha_beta_df, dd_df, fm) -> pd.DataFrame:
    """
    Composite Score (0–100):
        30% × 3yr return rank    (higher return → better rank → higher score)
        25% × Sharpe rank        (higher Sharpe → better)
        20% × Alpha rank         (higher Alpha → better)
        15% × Expense ratio rank (INVERSE: lower expense → higher score)
        10% × Max DD rank        (INVERSE: smaller drawdown → higher score)

    Ranking approach:
        For each metric, rank all 40 funds 1–40.
        Convert rank to score: score = (N - rank + 1) / N × 100
        where N = total number of funds.
        Rank 1 → score = 100, Rank 40 → score = 2.5.
        Then weight and sum.
    """
    print("\n" + "─"*65)
    print("  TASK 7 — Fund Scorecard (Composite 0-100)")
    print("─"*65)

    N = 40   # total funds

    def rank_to_score(series, ascending=False):
        """Convert a metric series to 0–100 score. ascending=False means higher value = rank 1."""
        ranked = series.rank(ascending=ascending, na_option="bottom")
        return ((N - ranked + 1) / N * 100).round(2)

    # Start from fund master as base (all 40 funds)
    scorecard = fm[["amfi_code", "scheme_name", "fund_house", "sub_category", "plan", "expense_ratio_pct"]].copy()

    # Merge 3yr CAGR
    scorecard = scorecard.merge(
        cagr_df[["amfi_code", "cagr_3yr_pct"]],
        on="amfi_code", how="left"
    )

    # Merge Sharpe
    scorecard = scorecard.merge(
        sharpe_df[["amfi_code", "sharpe_ratio"]],
        on="amfi_code", how="left"
    )

    # Merge Alpha
    scorecard = scorecard.merge(
        alpha_beta_df[["amfi_code", "alpha_annual_pct", "beta", "tracking_error_pct"]],
        on="amfi_code", how="left"
    )

    # Merge Max Drawdown
    scorecard = scorecard.merge(
        dd_df[["amfi_code", "max_drawdown_pct"]],
        on="amfi_code", how="left"
    )

    # ── Compute component scores ───────────────────────────────────────────────
    scorecard["score_return"]   = rank_to_score(scorecard["cagr_3yr_pct"],       ascending=False)  # higher = better
    scorecard["score_sharpe"]   = rank_to_score(scorecard["sharpe_ratio"],        ascending=False)  # higher = better
    scorecard["score_alpha"]    = rank_to_score(scorecard["alpha_annual_pct"],    ascending=False)  # higher = better
    scorecard["score_expense"]  = rank_to_score(scorecard["expense_ratio_pct"],   ascending=True)   # LOWER expense = better score
    scorecard["score_drawdown"] = rank_to_score(scorecard["max_drawdown_pct"],    ascending=False)  # LESS negative = better (closer to 0)

    # ── Weighted composite score ───────────────────────────────────────────────
    scorecard["composite_score"] = (
        0.30 * scorecard["score_return"]   +
        0.25 * scorecard["score_sharpe"]   +
        0.20 * scorecard["score_alpha"]    +
        0.15 * scorecard["score_expense"]  +
        0.10 * scorecard["score_drawdown"]
    ).round(2)

    # Final rank
    scorecard["final_rank"] = scorecard["composite_score"].rank(ascending=False).astype(int)
    scorecard = scorecard.sort_values("final_rank")

    # ── Print top 15 ──────────────────────────────────────────────────────────
    print(f"\n  FUND SCORECARD — TOP 15:")
    print(f"  {'Rk':<4} {'Fund':<42} {'Score':>6} {'3yrCAGR':>8} {'Sharpe':>7} {'Alpha':>7} {'Exp%':>5} {'DD%':>7}")
    print(f"  {'─'*4} {'─'*42} {'─'*6} {'─'*8} {'─'*7} {'─'*7} {'─'*5} {'─'*7}")
    for _, row in scorecard.head(15).iterrows():
        cagr = f"{row['cagr_3yr_pct']:.1f}%" if pd.notna(row["cagr_3yr_pct"]) else "  N/A"
        print(f"  {int(row['final_rank']):<4} {str(row['scheme_name'])[:41]:<42} "
              f"{row['composite_score']:>6.1f} "
              f"{cagr:>8} "
              f"{row['sharpe_ratio']:>7.3f} "
              f"{row['alpha_annual_pct']:>6.2f}% "
              f"{row['expense_ratio_pct']:>5.2f} "
              f"{row['max_drawdown_pct']:>6.1f}%")

    out_path = os.path.join(PROCESSED, "fund_scorecard.csv")
    scorecard.to_csv(out_path, index=False)
    print(f"\n    Saved: fund_scorecard.csv")

    return scorecard


# ══════════════════════════════════════════════════════════════════════════════
# TASK 8 — Benchmark Comparison Chart
# ══════════════════════════════════════════════════════════════════════════════
def plot_benchmark_comparison(nav: pd.DataFrame, bi: pd.DataFrame,
                               scorecard: pd.DataFrame, fm: pd.DataFrame):
    """
    Chart: Top 5 funds vs NIFTY50 and NIFTY100 over 3 years.

    All series are normalised to 100 at the start of the 3yr window
    so they can be compared on the same axis.

    Also computes Tracking Error = std(fund_return - bm_return) × √252
    """
    print("\n" + "─"*65)
    print("  TASK 8 — Benchmark Comparison Chart")
    print("─"*65)

    # Pick top 5 funds from scorecard
    top5 = scorecard.head(5)["amfi_code"].tolist()
    top5_names = {
        row["amfi_code"]: str(row["scheme_name"])[:35]
        for _, row in scorecard.head(5).iterrows()
    }

    latest = nav["date"].max()
    start_3yr = latest - pd.DateOffset(years=3)

    # Filter NAV to 3yr window
    nav_3yr = nav[nav["date"] >= start_3yr].copy()

    # Benchmark series
    nifty50  = bi[(bi["index_name"] == "NIFTY50")  & (bi["date"] >= start_3yr)].copy()
    nifty100 = bi[(bi["index_name"] == "NIFTY100") & (bi["date"] >= start_3yr)].copy()

    def normalise(series: pd.Series) -> pd.Series:
        """Index to 100 at start for comparison."""
        return series / series.iloc[0] * 100

    # ── Figure setup ──────────────────────────────────────────────────────────
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(13, 10),
        gridspec_kw={"height_ratios": [3, 1]},
        facecolor="#0f1117"
    )
    fig.patch.set_facecolor("#0f1117")

    colors_funds = ["#00d4ff", "#ff6b6b", "#ffd93d", "#6bcb77", "#c77dff"]
    colors_bm    = {"NIFTY50": "#ff9500", "NIFTY100": "#ff5e5e"}

    # ── Top chart: Normalised NAV lines ───────────────────────────────────────
    ax1.set_facecolor("#0f1117")
    ax1.tick_params(colors="white")
    ax1.spines[["top","right","left","bottom"]].set_color("#333")
    ax1.grid(axis="y", color="#222", linewidth=0.5)
    ax1.grid(axis="x", color="#222", linewidth=0.5)

    # Plot benchmarks first (behind funds)
    for bm_df, bm_name in [(nifty50, "NIFTY50"), (nifty100, "NIFTY100")]:
        if len(bm_df) == 0:
            continue
        bm_df = bm_df.sort_values("date")
        ax1.plot(bm_df["date"], normalise(bm_df["close_value"]),
                 label=bm_name,
                 color=colors_bm[bm_name],
                 linewidth=2.2,
                 linestyle="--",
                 alpha=0.85)

    # Plot top 5 funds
    tracking_errors = []
    for i, code in enumerate(top5):
        fund_nav = nav_3yr[nav_3yr["amfi_code"] == code].sort_values("date")
        if len(fund_nav) < 10:
            continue

        ax1.plot(fund_nav["date"], normalise(fund_nav["nav"]),
                 label=top5_names.get(code, str(code)),
                 color=colors_funds[i],
                 linewidth=1.8,
                 alpha=0.9)

        # Tracking error vs NIFTY100
        fund_ret = fund_nav.set_index("date")["nav"].pct_change().dropna()
        bm_ret   = nifty100.set_index("date")["close_value"].pct_change().dropna()
        aligned  = pd.concat([fund_ret, bm_ret], axis=1, join="inner").dropna()
        aligned.columns = ["fund", "bm"]
        if len(aligned) > 10:
            te = (aligned["fund"] - aligned["bm"]).std() * np.sqrt(TRADING_DAYS) * 100
            tracking_errors.append({
                "amfi_code": code,
                "scheme_name": top5_names.get(code, str(code)),
                "tracking_error_vs_nifty100_pct": round(te, 4)
            })

    ax1.set_title("Top 5 Funds vs NIFTY50 & NIFTY100 — 3 Year Performance (Indexed to 100)",
                  fontsize=13, color="white", pad=12)
    ax1.set_ylabel("Indexed Value (Start = 100)", color="white", fontsize=11)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=30, ha="right", color="white")
    ax1.yaxis.set_tick_params(labelcolor="white")
    ax1.legend(loc="upper left", fontsize=9, framealpha=0.2,
               labelcolor="white", facecolor="#1a1a2e")

    # ── Bottom chart: Tracking Error Bar ─────────────────────────────────────
    ax2.set_facecolor("#0f1117")
    ax2.tick_params(colors="white")
    ax2.spines[["top","right","left","bottom"]].set_color("#333")
    ax2.grid(axis="x", color="#222", linewidth=0.5)

    if tracking_errors:
        te_df = pd.DataFrame(tracking_errors)
        bars = ax2.barh(
            [n[:30] for n in te_df["scheme_name"]],
            te_df["tracking_error_vs_nifty100_pct"],
            color=colors_funds[:len(te_df)],
            alpha=0.8,
            edgecolor="#333"
        )
        for bar, val in zip(bars, te_df["tracking_error_vs_nifty100_pct"]):
            ax2.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
                     f"{val:.2f}%", va="center", color="white", fontsize=9)

    ax2.set_title("Tracking Error vs NIFTY100 (annualised %)", color="white", fontsize=11)
    ax2.set_xlabel("Tracking Error %", color="white", fontsize=10)
    ax2.yaxis.set_tick_params(labelcolor="white", labelsize=8)
    ax2.xaxis.set_tick_params(labelcolor="white")

    plt.tight_layout(pad=2.0)
    out_path = os.path.join(REPORTS, "benchmark_chart.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#0f1117")
    plt.close()
    print(f"   Saved: benchmark_chart.png")

    # Print tracking errors
    if tracking_errors:
        print(f"\n  Tracking Error vs NIFTY100 (annualised):")
        for te in tracking_errors:
            print(f"    {str(te['scheme_name'])[:45]:<45} {te['tracking_error_vs_nifty100_pct']:.4f}%")

    return tracking_errors


# ══════════════════════════════════════════════════════════════════════════════
# MAIN — Run all tasks in order
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("\n" + "═"*65)
    print("  BLUESTOCK FINTECH — DAY 4: FUND PERFORMANCE ANALYTICS")
    print("═"*65)

    # Load
    nav, fm, bi = load_data()

    # Task 1 — Daily returns
    returns = compute_daily_returns(nav)

    # Task 2 — CAGR
    cagr_df = compute_cagr(nav, fm)

    # Task 3 — Sharpe
    sharpe_df = compute_sharpe(returns, fm)

    # Task 4 — Sortino
    sortino_df = compute_sortino(returns, fm)

    # Task 5 — Alpha & Beta
    alpha_beta_df = compute_alpha_beta(returns, bi, fm)

    # Task 6 — Max Drawdown
    dd_df = compute_max_drawdown(nav, fm)

    # Task 7 — Scorecard
    scorecard = build_fund_scorecard(cagr_df, sharpe_df, alpha_beta_df, dd_df, fm)

    # Task 8 — Benchmark chart
    plot_benchmark_comparison(nav, bi, scorecard, fm)

    # ── Final summary ─────────────────────────────────────────────────────────
    print("\n" + "═"*65)
    print("  DAY 4 COMPLETE — ALL DELIVERABLES SAVED")
    print("═"*65)
    print(f"  data/processed/returns_computed.csv")
    print(f"  data/processed/cagr_report.csv")
    print(f"  data/processed/sharpe_values.csv")
    print(f"  data/processed/sortino_values.csv")
    print(f"  data/processed/alpha_beta.csv")
    print(f"  data/processed/max_drawdown.csv")
    print(f"  data/processed/fund_scorecard.csv")
    print(f"  reports/benchmark_chart.png")
    print()
    print(f"  → Open notebooks/04_performance_analytics.ipynb next")
    print("═"*65 + "\n")


if __name__ == "__main__":
    main()