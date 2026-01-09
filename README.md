# Gym Member Retention App

AI-powered Streamlit dashboard that predicts churn risk, highlights at-risk members, and surfaces behavioral insights from gym usage data.

## What's inside
- Churn prediction via a Random Forest model with visit-based features.
- Interactive dashboards: retention overview, at-risk member drill-down with exports, feature importance, and behavioral segmentation (classes, tenure, age, activity heatmaps, and user evolution).
- Sample data generator plus support for uploading your own member and visit history.
- Multilingual UI (English/Spanish/Catalan) and lightweight, file-based authentication for demos.

## Project structure
- `src/streamlit_app.py` - main Streamlit experience.
- `src/churn_model.py` - model training, evaluation, feature importance, and risk scoring.
- `src/create_sample_data.py` - CLI to generate demo CSVs into `data/`.
- `auxiliar/auxiliar.py` - synthetic data generator and feature engineering utilities.
- `data/` - expected location for `user_information.csv` and `user_visits.csv` (gitignored).
- `output/` - persisted model artifacts (e.g., `churn_model.joblib`).
- `notebooks/` - exploration and modeling notebooks.
- `users.json` - demo auth store created/updated at runtime.
- `run_app.py` - helper launcher (e.g., for cloud environments).

## Quick start
1) Create a virtual env (Python 3.10+ recommended):
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
```
2) Install dependencies:
```bash
pip install -r requirements.txt
```
3) Generate demo data (writes to `data/`):
```bash
python src/create_sample_data.py
```
4) Run the app:
```bash
streamlit run src/streamlit_app.py
```
5) Log in with the default demo user (`admin` / `admin123`) or create a new account from the sidebar. Users are stored in `users.json`.

## Data requirements
Place two CSVs under `data/` (the generator in step 3 produces them):
- `user_information.csv` - `USER_ID`, `REGISTRATION_DATE`, `MEMBERSHIP_END_DATE` (nullable), `AGE`, `GENDER`, `ZUMBA`, `BODY_PUMP`, `PILATES`, `SPINNING`.
- `user_visits.csv` - `USER_ID`, `ENTRY_TIME`, `EXIT_TIME`.
Dates must be parseable (YYYY-MM-DD or ISO timestamp). Additional columns are ignored.

## How the app works
- Loads data, engineers visit- and member-level features, then loads an existing model from `output/churn_model.joblib` or trains a new Random Forest automatically.
- Calculates churn risk per active member (risk levels: Low/Medium/High) and surfaces:
  - Retention overview metrics and churn-rate distribution.
  - Top at-risk users with pagination and Excel export.
  - Feature importance (model interpretability).
  - Behavioral views: class enrollment, tenure, age segments, user evolution over the last 12 months, and visit activity heatmaps/time-series.
- Includes a modal that explains the model pipeline and assumptions.

## Internationalization
Language strings live in `app/lang.py` and support English (default), Spanish, and Catalan. The language switcher is available in the UI and falls back to English for missing keys.

## Troubleshooting
- Missing data files: run `python src/create_sample_data.py` or upload CSVs via the onboarding flow.
- Model not found: the app will train one automatically and save it to `output/`.
- Authentication issues: delete `users.json` to reset demo users or re-create the default `admin` user on next launch.
