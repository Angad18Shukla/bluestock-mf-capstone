"""
advanced_analytics.py
=====================
Day 6 — Advanced Analytics + Risk Metrics
Bluestock Fintech Capstone Project

HOW TO RUN:
    From your project root (bluestock_mf_capstone/):
        python scripts/advanced_analytics.py

WHAT IT PRODUCES (all in data/processed/ and reports/):
    var_cvar_report.csv       — Historical VaR 95% + CVaR for all 40 funds
    rolling_sharpe_chart.png  — Rolling 90-day Sharpe for 5 key funds
    cohort_analysis.csv       — Investor cohort breakdown by first-tx year
    sip_continuity.csv        — Per-investor SIP gap analysis + at-risk flag
    sector_hhi.csv            — HHI concentration index per equity fund
    sector_hhi_chart.png      — HHI bar chart coloured by concentration level
"""

import os, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

warnings.filterwarnings("ignore")

#  Paths
ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW       = os.path.join(ROOT, "data", "raw")
PROCESSED = os.path.join(ROOT, "data", "processed")
REPORTS   = os.path.join(ROOT, "reports")
os.makedirs(PROCESSED, exist_ok=True)
os.makedirs(REPORTS,   exist_ok=True)

TRADING_DAYS = 252
RF_DAILY     = 0.065 / TRADING_DAYS   # 6.5% annual → daily

#  Dark chart style (consistent with Day 4) 
BG    = "#0f1117"
GRID  = "#1e1e2e"
TEXT  = "#e0e0e0"
MUTED = "#888888"

FUND_COLORS = ["#00d4ff", "#ff6b6b", "#ffd93d", "#6bcb77", "#c77dff"]

def dark_ax(ax):
    ax.set_facecolor(BG)
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    ax.title.set_color(TEXT)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.grid(color=GRID, linewidth=0.6, alpha=0.8)
    return ax


# TASK 1 — Historical VaR (95%) and CVaR

def compute_var_cvar(nav: pd.DataFrame, fm: pd.DataFrame) -> pd.DataFrame:
    """
    Historical VaR (95%):
        VaR_95 = 5th percentile of the daily return distribution

        Interpretation: "On 95% of trading days, the fund will NOT
        lose more than VaR_95% of its value."

    CVaR (Conditional VaR / Expected Shortfall):
        CVaR = mean of all returns BELOW the VaR threshold

        Interpretation: "On the worst 5% of days, the average loss
        is CVaR%. It answers: when things go bad, HOW bad?"

    CVaR is always worse (more negative) than VaR.
    A fund with low VaR but very high CVaR has fat tail risk —
    rare but catastrophic drawdowns.
    """
    print("\n" + "═" * 65)
    print("  TASK 1 — Historical VaR (95%) and CVaR")
    print("═" * 65)

    # Compute daily returns per fund
    nav = nav.sort_values(["amfi_code", "date"])
    nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()
    returns = nav.dropna(subset=["daily_return"])

    records = []
    for code, grp in returns.groupby("amfi_code"):
        r = grp["daily_return"].values

        # VaR: 5th percentile (negative value = loss)
        var_95  = np.percentile(r, 5)

        # CVaR: mean of returns that are BELOW the VaR threshold
        tail    = r[r <= var_95]
        cvar_95 = tail.mean() if len(tail) > 0 else np.nan

        # Additional distribution stats
        mean_r   = r.mean()
        std_r    = r.std()
        skew     = pd.Series(r).skew()
        kurt     = pd.Series(r).kurtosis()   # excess kurtosis; >0 = fat tails

        # Annualised vol
        ann_vol  = std_r * np.sqrt(TRADING_DAYS) * 100

        records.append({
            "amfi_code"          : code,
            "var_95_pct"         : round(var_95  * 100, 4),   # % daily loss at 95% confidence
            "cvar_95_pct"        : round(cvar_95 * 100, 4),   # % avg loss on worst 5% days
            "var_cvar_ratio"     : round(cvar_95 / var_95, 4) if var_95 != 0 else np.nan,
            "ann_vol_pct"        : round(ann_vol, 4),
            "skewness"           : round(skew, 4),
            "excess_kurtosis"    : round(kurt, 4),
            "tail_days_count"    : len(tail),
            "total_days"         : len(r),
        })

    var_df = pd.DataFrame(records)
    var_df = var_df.merge(
        fm[["amfi_code", "scheme_name", "fund_house", "sub_category", "risk_category", "plan"]],
        on="amfi_code", how="left"
    )

    # Rank by VaR (least risky first = var_95 closest to 0)
    var_df["var_rank"] = var_df["var_95_pct"].rank(ascending=False).astype(int)
    var_df = var_df.sort_values("var_95_pct", ascending=False)

    #  Print table 
    print(f"\n  VaR & CVaR Report — all 40 funds (sorted: safest → riskiest)")
    print(f"\n  {'Fund':<44} {'VaR 95%':>8} {'CVaR 95%':>9} {'Ann.Vol%':>9} {'Kurt':>6}")
    print(f"  {'─'*44} {'─'*8} {'─'*9} {'─'*9} {'─'*6}")
    for _, row in var_df.iterrows():
        name = str(row["scheme_name"])[:43]
        print(f"  {name:<44} {row['var_95_pct']:>7.3f}% "
              f"{row['cvar_95_pct']:>8.3f}% "
              f"{row['ann_vol_pct']:>8.2f}% "
              f"{row['excess_kurtosis']:>6.2f}")

    #  Key insights 
    riskiest  = var_df.iloc[-1]   # most negative VaR
    safest    = var_df.iloc[0]    # least negative VaR
    fat_tail  = var_df.loc[var_df["excess_kurtosis"].idxmax()]
    print(f"\n  Key findings:")
    print(f"    Riskiest (worst VaR) : {riskiest['scheme_name'][:50]}  VaR={riskiest['var_95_pct']:.3f}%")
    print(f"    Safest   (best  VaR) : {safest['scheme_name'][:50]}  VaR={safest['var_95_pct']:.3f}%")
    print(f"    Fattest tail (Kurt)  : {fat_tail['scheme_name'][:50]}  Kurt={fat_tail['excess_kurtosis']:.2f}")

    out = os.path.join(PROCESSED, "var_cvar_report.csv")
    var_df.to_csv(out, index=False)
    print(f"\n  ✅  Saved: var_cvar_report.csv")
    return var_df



# TASK 2 — Rolling 90-Day Sharpe Ratio

def compute_rolling_sharpe(nav: pd.DataFrame, fm: pd.DataFrame) -> None:
    """
    Rolling 90-day Sharpe:
        rolling_sharpe = (rolling_mean - RF_daily) / rolling_std * sqrt(252)

    Uses a 90-trading-day window. The first 89 rows per fund are NaN
    (not enough data to fill the window).

    Why rolling Sharpe matters:
        A single Sharpe over the full period hides HOW CONSISTENT the
        fund's risk-adjusted performance was. A fund with Sharpe=1.2 might
        have had Sharpe=2.5 for two years then Sharpe=-0.1 in a drawdown.
        Rolling Sharpe reveals this instability.

    5 funds chosen for diversity:
        - SBI Bluechip       (Large Cap, Moderate)
        - SBI Small Cap      (Small Cap, Very High)
        - SBI Magnum Gilt    (Gilt / Debt, Low)
        - HDFC Mid-Cap Opps  (Mid Cap, High)
        - Mirae Emerging     (Large & Mid Cap, Moderately High)
    """
    print("\n" + "═" * 65)
    print("  TASK 2 — Rolling 90-Day Sharpe Ratio (5 funds)")
    print("═" * 65)

    # 5 funds — chosen to show full spectrum of risk profiles
    FIVE_FUNDS = {
        119551: "SBI Bluechip (Large Cap)",
        119598: "SBI Small Cap (Very High)",
        119120: "SBI Gilt (Debt/Low)",
        100033: "HDFC Mid-Cap (High)",
        148568: "Mirae Emerging (Mod-High)",
    }

    nav = nav.sort_values(["amfi_code", "date"])
    nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()

    fig, (ax_main, ax_sub) = plt.subplots(
        2, 1, figsize=(13, 9),
        gridspec_kw={"height_ratios": [3, 1]},
        facecolor=BG
    )
    fig.patch.set_facecolor(BG)

    # Main chart: Rolling Sharpe lines 
    dark_ax(ax_main)
    ax_main.axhline(0,   color=MUTED, linewidth=0.8, linestyle="--", alpha=0.6)
    ax_main.axhline(1.0, color="#ffd93d", linewidth=0.6, linestyle=":", alpha=0.5)
    ax_main.text(nav["date"].min(), 1.05, "Sharpe = 1.0 (good)", color="#ffd93d",
                 fontsize=8, alpha=0.7)

    rolling_data = {}
    for i, (code, label) in enumerate(FIVE_FUNDS.items()):
        grp = nav[nav["amfi_code"] == code].sort_values("date")
        r   = grp["daily_return"]

        roll_mean  = r.rolling(90).mean()
        roll_std   = r.rolling(90).std()
        roll_sharpe = (roll_mean - RF_DAILY) / roll_std * np.sqrt(TRADING_DAYS)

        ax_main.plot(
            grp["date"], roll_sharpe,
            color=FUND_COLORS[i], linewidth=1.6,
            label=label, alpha=0.9
        )
        rolling_data[label] = roll_sharpe.dropna().values

        # Print stats
        valid = roll_sharpe.dropna()
        print(f"  {label[:40]:<40} mean={valid.mean():.3f}  min={valid.min():.3f}  max={valid.max():.3f}")

    ax_main.set_title("Rolling 90-Day Sharpe Ratio — 5 Fund Profiles (2022–2026)",
                      fontsize=13, color=TEXT, pad=10)
    ax_main.set_ylabel("Rolling Sharpe (90-day window)", color=TEXT, fontsize=10)
    ax_main.legend(loc="upper left", fontsize=9, framealpha=0.15,
                   labelcolor=TEXT, facecolor="#1a1a2e")
    ax_main.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax_main.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.setp(ax_main.xaxis.get_majorticklabels(), rotation=30, ha="right", color=TEXT)

    #  Sub chart: Sharpe distribution (violin-like histogram)
    dark_ax(ax_sub)
    ax_sub.axhline(0, color=MUTED, linewidth=0.6, linestyle="--", alpha=0.5)

    # Show periods when ALL 5 funds had Sharpe < 0 simultaneously (market stress)
    # Use the Gilt fund as a reference for market calm
    gilt_grp = nav[nav["amfi_code"] == 119120].sort_values("date")
    gilt_r   = gilt_grp["daily_return"]
    gilt_rs  = (gilt_r.rolling(90).mean() - RF_DAILY) / gilt_r.rolling(90).std() * np.sqrt(TRADING_DAYS)
    ax_sub.fill_between(gilt_grp["date"], gilt_rs, 0,
                         where=(gilt_rs < 0), alpha=0.25, color="#ff6b6b",
                         label="Gilt Sharpe < 0 (stress)")
    ax_sub.plot(gilt_grp["date"], gilt_rs, color="#6bcb77", linewidth=1, alpha=0.7,
                label="Gilt fund (benchmark for calm)")
    ax_sub.set_ylabel("Gilt fund\nRolling Sharpe", color=TEXT, fontsize=8)
    ax_sub.legend(loc="upper right", fontsize=8, framealpha=0.15,
                  labelcolor=TEXT, facecolor="#1a1a2e")
    ax_sub.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax_sub.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    plt.setp(ax_sub.xaxis.get_majorticklabels(), rotation=30, ha="right", color=TEXT)

    plt.tight_layout(pad=2.0)
    out = os.path.join(REPORTS, "rolling_sharpe_chart.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"\n  ✅  Saved: rolling_sharpe_chart.png")



# TASK 3 — Investor Cohort Analysis

def cohort_analysis(tx: pd.DataFrame, fm: pd.DataFrame) -> pd.DataFrame:
    """
    Cohort = group of investors who made their FIRST transaction in the same year.

    Why cohort analysis?
        Investors who started in different market conditions behave differently.
        A 2024 cohort entered during a bull run; their SIP amounts, fund
        preferences, and continuation rates differ from a stress-period cohort.

    Metrics per cohort:
        - Cohort size (how many investors)
        - Avg SIP amount (only SIP transactions)
        - Total amount invested (all transaction types)
        - Top 3 preferred funds (by SIP count)
        - KYC verified % (proxy for investor quality)
        - Avg annual income
    """
    print("\n" + "═" * 65)
    print("  TASK 3 — Investor Cohort Analysis")
    print("═" * 65)

    # Step 1: find each investor's first transaction date → cohort year
    first_tx = (
        tx.groupby("investor_id")["transaction_date"]
        .min()
        .reset_index()
        .rename(columns={"transaction_date": "first_tx_date"})
    )
    first_tx["cohort_year"] = first_tx["first_tx_date"].dt.year

    # Step 2: join cohort year back onto every transaction
    tx_c = tx.merge(first_tx[["investor_id", "cohort_year"]], on="investor_id", how="left")
    sip_only = tx_c[tx_c["transaction_type"] == "SIP"]

    cohort_records = []
    for year, grp in tx_c.groupby("cohort_year"):
        sip_grp        = grp[grp["transaction_type"] == "SIP"]
        investors      = grp["investor_id"].nunique()
        avg_sip        = sip_grp["amount_inr"].mean()
        total_invested = grp["amount_inr"].sum()
        kyc_pct        = (grp["kyc_status"] == "Verified").mean() * 100
        avg_income     = grp["annual_income_lakh"].mean()

        # Top 3 funds by SIP frequency in this cohort
        top_funds = (
            sip_grp.groupby("amfi_code")
            .size()
            .sort_values(ascending=False)
            .head(3)
        )
        top_fund_names = []
        for code, count in top_funds.items():
            name_row = fm[fm["amfi_code"] == code]["scheme_name"]
            name = name_row.values[0][:35] if len(name_row) > 0 else str(code)
            top_fund_names.append(f"{name} ({count} SIPs)")

        cohort_records.append({
            "cohort_year"           : year,
            "investors_count"       : investors,
            "avg_sip_amount_inr"    : round(avg_sip, 2),
            "total_invested_cr"     : round(total_invested / 1e7, 4),  # to crores
            "kyc_verified_pct"      : round(kyc_pct, 2),
            "avg_annual_income_lakh": round(avg_income, 2),
            "top_fund_1"            : top_fund_names[0] if len(top_fund_names) > 0 else "-",
            "top_fund_2"            : top_fund_names[1] if len(top_fund_names) > 1 else "-",
            "top_fund_3"            : top_fund_names[2] if len(top_fund_names) > 2 else "-",
        })

    cohort_df = pd.DataFrame(cohort_records)

    # Print cohort comparison 
    print(f"\n  COHORT COMPARISON TABLE:")
    print(f"  {'Cohort':<10} {'Investors':>10} {'Avg SIP ₹':>12} {'Total Cr':>10} {'KYC%':>7} {'Avg Inc L':>10}")
    print(f"  {'─'*10} {'─'*10} {'─'*12} {'─'*10} {'─'*7} {'─'*10}")
    for _, row in cohort_df.iterrows():
        print(f"  {int(row['cohort_year']):<10} {int(row['investors_count']):>10,} "
              f"₹{row['avg_sip_amount_inr']:>10,.0f} "
              f"{row['total_invested_cr']:>10.2f} "
              f"{row['kyc_verified_pct']:>6.1f}% "
              f"₹{row['avg_annual_income_lakh']:>8.1f}L")

    print(f"\n  Top fund preferences per cohort:")
    for _, row in cohort_df.iterrows():
        print(f"\n  {int(row['cohort_year'])} cohort:")
        print(f"    1. {row['top_fund_1']}")
        print(f"    2. {row['top_fund_2']}")
        print(f"    3. {row['top_fund_3']}")

    out = os.path.join(PROCESSED, "cohort_analysis.csv")
    cohort_df.to_csv(out, index=False)
    print(f"\n  ✅  Saved: cohort_analysis.csv")
    return cohort_df



# TASK 4 — SIP Continuity Analysis

def sip_continuity(tx: pd.DataFrame) -> pd.DataFrame:
    """
    SIP Continuity = how regularly does an investor make their SIP payments?

    Logic:
        1. Filter to SIP transactions only
        2. For each investor with 6+ SIP transactions:
           - Sort their SIP dates chronologically
           - Compute the gap (in days) between consecutive SIPs
           - Compute avg_gap = mean of all gaps
        3. Flag as "at_risk" if avg_gap > 35 days
           (normal SIP cycle is monthly = ~30 days; >35 = likely missed a cycle)

    Business value:
        At-risk investors are likely to stop their SIPs entirely.
        AMCs can proactively reach out to prevent churn.
    """
    print("\n" + "═" * 65)
    print("  TASK 4 — SIP Continuity Analysis")
    print("═" * 65)

    sip = tx[tx["transaction_type"] == "SIP"].copy()
    sip = sip.sort_values(["investor_id", "transaction_date"])

    # Only analyse investors with 6+ SIP transactions
    sip_counts = sip.groupby("investor_id").size()
    eligible   = sip_counts[sip_counts >= 6].index
    sip_eligible = sip[sip["investor_id"].isin(eligible)]

    print(f"  Total investors with SIP transactions : {sip['investor_id'].nunique():,}")
    print(f"  Investors with 6+ SIP transactions   : {len(eligible):,}")

    records = []
    for inv_id, grp in sip_eligible.groupby("investor_id"):
        grp  = grp.sort_values("transaction_date")
        dates = grp["transaction_date"].values

        # Compute day gaps between consecutive SIP dates
        gaps = np.diff(dates.astype("datetime64[D]")).astype(int)

        avg_gap    = gaps.mean()
        max_gap    = gaps.max()
        min_gap    = gaps.min()
        std_gap    = gaps.std()
        num_sips   = len(dates)
        at_risk    = avg_gap > 35

        records.append({
            "investor_id"       : inv_id,
            "num_sip_tx"        : num_sips,
            "avg_gap_days"      : round(avg_gap, 1),
            "max_gap_days"      : int(max_gap),
            "min_gap_days"      : int(min_gap),
            "std_gap_days"      : round(std_gap, 1),
            "at_risk"           : at_risk,
            "state"             : grp["state"].iloc[0],
            "age_group"         : grp["age_group"].iloc[0],
            "city_tier"         : grp["city_tier"].iloc[0],
        })

    cont_df = pd.DataFrame(records)

    #  Summary stats 
    n_at_risk      = cont_df["at_risk"].sum()
    n_regular      = (~cont_df["at_risk"]).sum()
    at_risk_pct    = n_at_risk / len(cont_df) * 100
    continuity_rate = 100 - at_risk_pct

    print(f"\n  SIP Continuity Summary:")
    print(f"    Eligible investors (6+ SIPs) : {len(cont_df):,}")
    print(f"    Regular investors (≤35d gap) : {n_regular:,}  ({continuity_rate:.1f}%)")
    print(f"    At-risk  investors (>35d gap): {n_at_risk:,}  ({at_risk_pct:.1f}%)")
    print(f"    Avg gap across all investors : {cont_df['avg_gap_days'].mean():.1f} days")
    print(f"    Median gap                   : {cont_df['avg_gap_days'].median():.1f} days")

    # At-risk breakdown by state and age group
    print(f"\n  At-risk investors by state:")
    state_risk = (cont_df.groupby("state")["at_risk"].agg(["sum","count"])
                  .rename(columns={"sum":"at_risk","count":"total"}))
    state_risk["at_risk_pct"] = (state_risk["at_risk"] / state_risk["total"] * 100).round(1)
    state_risk = state_risk.sort_values("at_risk_pct", ascending=False)
    print(state_risk.to_string())

    print(f"\n  At-risk investors by age group:")
    age_risk = (cont_df.groupby("age_group")["at_risk"].agg(["sum","count"])
                .rename(columns={"sum":"at_risk","count":"total"}))
    age_risk["at_risk_pct"] = (age_risk["at_risk"] / age_risk["total"] * 100).round(1)
    age_risk = age_risk.sort_values("at_risk_pct", ascending=False)
    print(age_risk.to_string())

    out = os.path.join(PROCESSED, "sip_continuity.csv")
    cont_df.to_csv(out, index=False)
    print(f"\n  ✅  Saved: sip_continuity.csv")
    return cont_df



# TASK 6 — Sector HHI Concentration

def sector_hhi(port: pd.DataFrame, fm: pd.DataFrame) -> pd.DataFrame:
    """
    Herfindahl-Hirschman Index (HHI):
        HHI = Σ (weight_i)²  for all sectors in a fund's portfolio

    Interpretation:
        HHI = 10,000 → 100% in one sector (perfectly concentrated)
        HHI < 1,500  → well-diversified (like an index fund)
        HHI 1,500–2,500 → moderately concentrated
        HHI > 2,500  → highly concentrated (sector bet)

    Note: weights are in % (e.g. 13.85), so we use them as-is
    and the max possible HHI = 10,000 (100²).

    Example:
        Fund with 5 equal sectors at 20% each:
        HHI = 5 × (20²) = 5 × 400 = 2,000 (moderate)

        Fund with one 50% sector + four 12.5% sectors:
        HHI = 50² + 4 × 12.5² = 2,500 + 625 = 3,125 (concentrated)
    """
    print("\n" + "═" * 65)
    print("  TASK 6 — Sector HHI Concentration")
    print("═" * 65)

    # Only equity funds (debt funds don't have sector holdings)
    equity_codes = fm[fm["category"] == "Equity"]["amfi_code"].tolist()
    port_eq      = port[port["amfi_code"].isin(equity_codes)].copy()

    print(f"  Equity funds with holdings data: {port_eq['amfi_code'].nunique()}")

    # Aggregate weight by sector per fund (sum across stocks in same sector)
    sector_wt = (
        port_eq.groupby(["amfi_code", "sector"])["weight_pct"]
        .sum()
        .reset_index()
    )

    # Compute HHI per fund: sum of squared sector weights
    def hhi(weights):
        return (weights ** 2).sum()

    hhi_df = (
        sector_wt.groupby("amfi_code")["weight_pct"]
        .apply(hhi)
        .reset_index()
        .rename(columns={"weight_pct": "hhi"})
    )

    # Number of sectors per fund
    num_sectors = sector_wt.groupby("amfi_code")["sector"].count().reset_index()
    num_sectors.columns = ["amfi_code", "num_sectors"]

    # Dominant sector per fund (highest weight_pct)
    dominant = (
        sector_wt.loc[sector_wt.groupby("amfi_code")["weight_pct"].idxmax()]
        [["amfi_code", "sector", "weight_pct"]]
        .rename(columns={"sector": "dominant_sector", "weight_pct": "dominant_weight_pct"})
    )

    hhi_df = hhi_df.merge(num_sectors, on="amfi_code")
    hhi_df = hhi_df.merge(dominant,    on="amfi_code")
    hhi_df = hhi_df.merge(
        fm[["amfi_code", "scheme_name", "sub_category", "fund_house"]],
        on="amfi_code", how="left"
    )

    # Concentration label
    def concentration_label(h):
        if h < 1500:   return "Diversified"
        elif h < 2500: return "Moderate"
        else:          return "Concentrated"

    hhi_df["concentration"] = hhi_df["hhi"].apply(concentration_label)
    hhi_df["hhi"]           = hhi_df["hhi"].round(2)
    hhi_df = hhi_df.sort_values("hhi", ascending=False).reset_index(drop=True)

    #  Print table 
    print(f"\n  SECTOR HHI TABLE (most → least concentrated):")
    print(f"\n  {'Fund':<44} {'HHI':>7} {'Sectors':>8} {'Dominant Sector':<20} {'Label'}")
    print(f"  {'─'*44} {'─'*7} {'─'*8} {'─'*20} {'─'*13}")
    for _, row in hhi_df.iterrows():
        print(f"  {str(row['scheme_name'])[:43]:<44} "
              f"{row['hhi']:>7.1f} "
              f"{row['num_sectors']:>8} "
              f"{str(row['dominant_sector']):<20} "
              f"{row['concentration']}")

    #  Chart 
    fig, ax = plt.subplots(figsize=(12, 10), facecolor=BG)
    dark_ax(ax)

    color_map = {"Diversified": "#6bcb77", "Moderate": "#ffd93d", "Concentrated": "#ff6b6b"}
    colors = [color_map[c] for c in hhi_df["concentration"]]
    short_names = [str(n)[:38] for n in hhi_df["scheme_name"]]

    bars = ax.barh(range(len(hhi_df)), hhi_df["hhi"],
                   color=colors, edgecolor=GRID, linewidth=0.5, alpha=0.88)

    # Threshold lines
    ax.axvline(1500, color="#ffd93d", linewidth=1, linestyle="--", alpha=0.6)
    ax.axvline(2500, color="#ff6b6b", linewidth=1, linestyle="--", alpha=0.6)
    ax.text(1510, len(hhi_df) - 0.5, "Moderate", color="#ffd93d", fontsize=8, va="top")
    ax.text(2510, len(hhi_df) - 0.5, "Concentrated", color="#ff6b6b", fontsize=8, va="top")

    # Value labels on bars
    for bar, val in zip(bars, hhi_df["hhi"]):
        ax.text(bar.get_width() + 30, bar.get_y() + bar.get_height() / 2,
                f"{val:.0f}", va="center", color=TEXT, fontsize=8)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#6bcb77", label="Diversified  (HHI < 1500)"),
        Patch(facecolor="#ffd93d", label="Moderate     (HHI 1500–2500)"),
        Patch(facecolor="#ff6b6b", label="Concentrated (HHI > 2500)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=9,
              framealpha=0.15, labelcolor=TEXT, facecolor="#1a1a2e")

    ax.set_yticks(range(len(hhi_df)))
    ax.set_yticklabels(short_names, fontsize=8, color=TEXT)
    ax.set_xlabel("HHI Score (higher = more concentrated)", color=TEXT)
    ax.set_title("Sector HHI Concentration — All Equity Funds", color=TEXT, fontsize=13, pad=12)
    ax.invert_yaxis()

    plt.tight_layout()
    chart_out = os.path.join(REPORTS, "sector_hhi_chart.png")
    plt.savefig(chart_out, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"\n    Saved: sector_hhi_chart.png")

    out = os.path.join(PROCESSED, "sector_hhi.csv")
    hhi_df.to_csv(out, index=False)
    print(f"    Saved: sector_hhi.csv")
    return hhi_df


# MAIN

def main():
    print("\n" + "═" * 65)
    print("  BLUESTOCK FINTECH — DAY 6: ADVANCED ANALYTICS")
    print("═" * 65)

    nav  = pd.read_csv(os.path.join(RAW, "02_nav_history.csv"))
    fm   = pd.read_csv(os.path.join(RAW, "01_fund_master.csv"))
    tx   = pd.read_csv(os.path.join(RAW, "08_investor_transactions.csv"))
    port = pd.read_csv(os.path.join(RAW, "09_portfolio_holdings.csv"))

    nav["date"]               = pd.to_datetime(nav["date"])
    tx["transaction_date"]    = pd.to_datetime(tx["transaction_date"])

    var_df    = compute_var_cvar(nav.copy(), fm)
    compute_rolling_sharpe(nav.copy(), fm)
    cohort_df = cohort_analysis(tx, fm)
    cont_df   = sip_continuity(tx)
    hhi_df    = sector_hhi(port, fm)

    print("\n" + "═" * 65)
    print("  DAY 6 COMPLETE — ALL DELIVERABLES")
    print("═" * 65)
    print("  data/processed/var_cvar_report.csv")
    print("  data/processed/cohort_analysis.csv")
    print("  data/processed/sip_continuity.csv")
    print("  data/processed/sector_hhi.csv")
    print("  reports/rolling_sharpe_chart.png")
    print("  reports/sector_hhi_chart.png")
    print("  → Run scripts/recommender.py separately")
    print("  → Open notebooks/05_advanced_analytics.ipynb for write-up")
    print("═" * 65 + "\n")


if __name__ == "__main__":
    main()