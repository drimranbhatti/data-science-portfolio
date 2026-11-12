# Data Science & Business Analytics Portfolio

Applied data-science projects focused on the questions **finance leaders and business owners** ask: who will churn and is it worth saving them, how healthy is recurring revenue, is customer satisfaction really changing, and what does the sales database say. Each project is a single executed notebook with its data, charts and plain-language recommendations.

| Project | Summary |
|---|---|
| [Customer churn prediction & profit-optimal retention](projects/01-customer-churn-prediction) | Telco churn (7,043 customers): EDA of churn drivers, logistic regression vs gradient boosting (ROC-AUC ≈ 0.85), cumulative gains, and a **profit curve** that picks who gets a retention offer. The best policy contacts 41% of customers and **doubles** campaign profit compared with contacting everyone. |
| [SaaS subscription metrics](projects/02-saas-subscription-metrics) | MRR, new vs churned MRR, logo churn, **cohort retention** heatmap and LTV by plan from 10,497 subscriptions. Annual plans carry about **3× the lifetime value** of monthly plans. |
| [Net Promoter Score with bootstrap confidence intervals](projects/03-net-promoter-score) | Monthly NPS with 95% bootstrap CIs, showing which month-to-month moves are real and which are sampling noise. |
| [SMS spam classifier (NLP)](projects/04-sms-spam-classifier) | Word + character n-gram TF-IDF with Naive Bayes, logistic regression and a linear SVM; **99% accuracy, 0.99 spam precision** on hold-out data; the trained pipeline is saved to `model/`. |
| [Pakistan Stock Exchange: risk & moving-average strategies](projects/05-psx-stock-analysis) | Six PSX stocks plus Apple: risk, correlation and drawdowns, then dual moving-average strategies with parameters chosen **in-sample** and judged **out-of-sample**, net of costs. Mixed results that show how single-sample backtests mislead. |
| [SQL business analytics (Chinook)](projects/06-sql-business-analytics) | Eight business questions in SQL: revenue by genre and country, running totals and MoM growth with **window functions**, sales-rep ranking, **RFM segmentation**, album-vs-track purchasing and catalogue utilisation. |
| [Monthly temperature trends, 1901-2017](projects/07-climate-temperature-trends) | Reshaping, seasonality, warming trend with autocorrelation-robust (Newey-West) CIs: **0.4 °C/century before 1960 vs 2.2 °C/century after**, plus a decadal anomaly heatmap. |

<p float="left">
  <img src="projects/01-customer-churn-prediction/images/profit_curve.png" width="49%" />
  <img src="projects/02-saas-subscription-metrics/images/cohorts.png" width="49%" />
</p>

## Skills shown
**Python** (pandas, NumPy, scikit-learn, statsmodels, matplotlib/seaborn) · **SQL** (CTEs, window functions, RFM) · classification and model evaluation (ROC/PR, cross-validation, calibration to business value) · **NLP** (TF-IDF, linear models) · **SaaS/finance KPIs** (MRR, churn, cohorts, LTV, NPS) · time-series trend inference · honest out-of-sample backtesting

## More quantitative-finance work
* [derivatives-pricing-toolkit](https://github.com/drimranbhatti/derivatives-pricing-toolkit): Black-Scholes, Heston, Merton, Bates, calibration
* [portfolio-optimization-lab](https://github.com/drimranbhatti/portfolio-optimization-lab): Markowitz, Black-Litterman, HRP, Kelly
* [market-risk-models](https://github.com/drimranbhatti/market-risk-models): VaR/ES backtesting, HMM regimes, Bayesian networks
* [covid-market-impact-research](https://github.com/drimranbhatti/covid-market-impact-research): contagion, GARCH, Diebold-Yilmaz spillovers
* [dea-panel-econometrics](https://github.com/drimranbhatti/dea-panel-econometrics): DEA efficiency, Malmquist, FE/RE panels
* [crypto-deep-learning-trading](https://github.com/drimranbhatti/crypto-deep-learning-trading) · [ml-finance-models](https://github.com/drimranbhatti/ml-finance-models)

## Data sources
IBM Telco Customer Churn sample · UCI SMS Spam Collection · Chinook sample database (L. Rocha) · PSX historical prices · public course datasets (subscriptions, NPS, monthly temperatures). Datasets are included for reproducibility and belong to their respective owners.

---
**Dr. Muhammad Imran Bhatti, PhD** · Finance & AI · [LinkedIn](https://www.linkedin.com/in/drimranbhatti) · [imranbhatti.com](https://imranbhatti.com) · MIT licensed (code)
