import pandas as pd

df = pd.read_csv("data/processed/clean_performance.csv")

risk = input("Risk Appetite (Low / Moderate / High): ")

recommend = (
    df[df["risk_grade"].str.contains(risk, case=False, na=False)]
    .sort_values("sharpe_ratio", ascending=False)
    .head(3)
)

print("\nTop 3 Recommended Funds\n")

print(
    recommend[
        [
            "scheme_name",
            "risk_grade",
            "sharpe_ratio",
            "return_3yr_pct"
        ]
    ]
)