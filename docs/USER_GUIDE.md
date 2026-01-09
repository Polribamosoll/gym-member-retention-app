# Gym Member Retention App - User Guide

This guide covers day-to-day usage of the Streamlit dashboard.

## 1) Sign in
- Default demo account: `admin` / `admin123`.
- You can register additional users in-app; credentials are stored locally in `users.json`.
- If you get locked out, delete `users.json` and restart the app to recreate the demo user.

## 2) Load data
- **Use demo data:** run `python src/create_sample_data.py` to generate `data/user_information.csv` and `data/user_visits.csv`.
- **Bring your own data:** place CSVs with the same column names under `data/`:
  - `user_information.csv`: `USER_ID`, `REGISTRATION_DATE`, `MEMBERSHIP_END_DATE` (nullable), `AGE`, `GENDER`, `ZUMBA`, `BODY_PUMP`, `PILATES`, `SPINNING`.
  - `user_visits.csv`: `USER_ID`, `ENTRY_TIME`, `EXIT_TIME`.
- The onboarding flow also lets you upload these files after sign-up.

## 3) Explore dashboards
**Retention Overview**
- Summary metrics: total users/visits, active vs churned, churn rate, users at risk.
- Risk distribution donut: Low/Medium/High churn-risk split.
- Top at-risk users: paginated table with styling by risk level plus Excel export.
- Feature importance: Random Forest feature importances to explain the model.

**Behavior & Segmentation**
- Churn rate by class enrollment (Zumba/Body Pump/Pilates/Spinning).
- Churn rate by tenure and age bands.
- Users evolution (last 12 months) showing Active/New/Churned counts.
- Activity heatmap and hourly buckets for recent visits.

## 4) Model lifecycle
- On startup the app loads `output/churn_model.joblib` if present; otherwise it trains a new Random Forest and saves it.
- Risk scores are recalculated each run from the loaded/trained model.
- You can view the "How the model works" modal from the retention page for a plain-language explanation.

## 5) Tips
- Ensure dates are parseable (YYYY-MM-DD or ISO timestamps).
- Keep the `data/` directory writable; model artifacts go to `output/`.
- Switch languages from the UI header (English/Spanish/Catalan).
- For a clean slate, delete `users.json`, `data/*.csv`, and `output/churn_model.joblib`, then re-run the data generator.
