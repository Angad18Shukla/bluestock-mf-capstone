# Mutual Fund Analytics Platform

## Bluestock Fintech Capstone Project

### Author

**Angad Shukla**

---

# Project Overview

The Mutual Fund Analytics Platform is an end-to-end fintech analytics project developed as part of the Bluestock Fintech Capstone Program.

The project uses Indian Mutual Fund datasets sourced from AMFI and mfapi.in to build a complete analytics workflow covering:

* Data Ingestion
* Data Cleaning
* Database Design
* Exploratory Data Analysis (EDA)
* Risk & Performance Analytics
* Advanced Analytics
* Interactive Power BI Dashboard
* Business Insights & Reporting

The objective is to help investors and analysts evaluate mutual fund performance, investor behaviour, portfolio risk, and industry growth trends using data-driven methods.

---

# Key Project Statistics

| Metric                | Value   |
| --------------------- | ------- |
| Mutual Fund Schemes   | 40      |
| NAV Records           | 46,000+ |
| Investor Transactions | 32,778  |
| Investors             | 5,000   |
| Fund Houses           | 10      |
| States Covered        | 12      |
| Dashboard Pages       | 4       |

---

# Technology Stack

* Python
* Pandas
* NumPy
* Matplotlib
* SQLite
* SQLAlchemy
* Jupyter Notebook
* Power BI
* Git & GitHub

---

# Project Structure

```text
bluestock-mf-capstone/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda_analysis.ipynb
│   ├── 04_performance_analytics.ipynb
│   └── 05_advanced_analytics.ipynb
│
├── scripts/
│   ├── data_ingestion.py
│   ├── data_cleaning.py
│   ├── load_database.py
│   ├── performance_analytics.py
│   ├── advanced_analytics.py
│   └── recommender.py
│
├── sql/
│   ├── schema.sql
│   └── queries.sql
│
├── dashboard/
│   └── bluestock_mf_dashboard.pbix
│
├── reports/
│
└── README.md
```

---

# Dataset Description

The project uses 10 datasets:

| File                         | Description                        |
| ---------------------------- | ---------------------------------- |
| 01_fund_master.csv           | Scheme details, AMC, risk category |
| 02_nav_history.csv           | Daily NAV history                  |
| 03_aum_by_fund_house.csv     | Quarterly AUM data                 |
| 04_monthly_sip_inflows.csv   | Monthly SIP inflows                |
| 05_category_inflows.csv      | Category-wise fund inflows         |
| 06_industry_folio_count.csv  | Mutual fund folio growth           |
| 07_scheme_performance.csv    | Returns and risk metrics           |
| 08_investor_transactions.csv | Investor transactions              |
| 09_portfolio_holdings.csv    | Portfolio stock holdings           |
| 10_benchmark_indices.csv     | Benchmark index data               |

---

# Setup Instructions

## 1. Clone Repository

```bash
git clone https://github.com/Angad18Shukla/bluestock-mf-capstone.git
cd bluestock-mf-capstone
```

## 2. Install Dependencies

```bash
pip install pandas numpy matplotlib sqlalchemy jupyter
```

## 3. Open Jupyter Notebook

```bash
jupyter notebook
```

---

# How to Run ETL Pipeline

Run the ETL scripts in sequence:

```bash
python scripts/data_ingestion.py
python scripts/data_cleaning.py
python scripts/load_database.py
```

These scripts:

* Load raw datasets
* Clean and validate records
* Create SQLite database
* Load processed data into database tables

---

# How to Run Analytics

Performance Analytics:

```bash
python scripts/performance_analytics.py
```

Advanced Analytics:

```bash
python scripts/advanced_analytics.py
```

Fund Recommendation System:

```bash
python scripts/recommender.py
```

---

# How to Open Dashboard

1. Open Power BI Desktop
2. Navigate to:

```text
dashboard/bluestock_mf_dashboard.pbix
```

3. Open the PBIX file
4. Refresh data if required

Dashboard Pages:

* Industry Overview
* Fund Performance
* Investor Analytics
* SIP Market Trends

---

# Key Findings

* SIP inflows reached ₹31,002 Crore by December 2025.
* SBI Mutual Fund recorded the highest AUM among all AMCs.
* Small Cap Funds generated the highest 3-year returns.
* ICICI Prudential Liquid Fund achieved the highest Sharpe Ratio.
* Investor cohort analysis identified differences in investment behaviour across years.
* Sector HHI analysis highlighted portfolio concentration risks.

---

# Future Enhancements

* Streamlit Web Application
* Power BI Service Deployment
* Automated ETL Scheduling
* Monte Carlo NAV Simulation
* Portfolio Optimisation Models

---

# Conclusion

This project successfully demonstrates the complete lifecycle of a fintech analytics solution, from raw data ingestion to business intelligence dashboards. The platform combines data engineering, statistical analysis, financial analytics, and visualization to generate actionable mutual fund insights.

---

## Bluestock Fintech Capstone Project

### Mutual Fund Analytics Platform

### June 2026


