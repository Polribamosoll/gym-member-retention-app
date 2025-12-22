import streamlit as st
import pandas as pd
from pathlib import Path
import hashlib
import joblib

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from auxiliar.auxiliar import engineer_features
from src.churn_model import train_churn_model, evaluate_model, get_feature_importance, predict_churn_risk, save_model, load_model, FEATURE_COLUMNS

# --- User Management (for demo purposes) ---
USERS = {
    "admin": hashlib.sha256("admin123".encode()).hexdigest()
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_page():
    st.sidebar.title("Login / Register")
    
    choice = st.sidebar.radio("Go to", ["Login", "Register"])

    if choice == "Login":
        st.sidebar.subheader("Login to the App")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        
        if st.sidebar.button("Login"):
            hashed_password = hash_password(password)
            if username in USERS and USERS[username] == hashed_password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success(f"Welcome {username}!")
                st.rerun()
            else:
                st.error("Invalid Username or Password")
    
    elif choice == "Register":
        st.sidebar.subheader("Create a New Account")
        new_username = st.sidebar.text_input("New Username")
        new_password = st.sidebar.text_input("New Password", type="password")
        
        if st.sidebar.button("Register"):
            if new_username in USERS:
                st.error("Username already exists. Please choose a different one.")
            else:
                USERS[new_username] = hash_password(new_password)
                st.success("Account created successfully! Please login.")

def main_app():
    st.title("Gym Churn Predictor Dashboard")
    st.write(f"Welcome, {st.session_state['username']}!")

    # --- Load Data ---
    data_dir = Path.cwd() / 'data'
    users_df = pd.read_csv(data_dir / 'user_information.csv', parse_dates=['REGISTRATION_DATE', 'MEMBERSHIP_END_DATE'])
    visits_df = pd.read_csv(data_dir / 'user_visits.csv', parse_dates=['ENTRY_TIME', 'EXIT_TIME'])

    st.subheader("Data Overview")
    st.write(f"Total Users: {len(users_df)}")
    st.write(f"Total Visits: {len(visits_df)}")
    st.write(f"Churned Users: {users_df['MEMBERSHIP_END_DATE'].notna().sum()}")
    st.write(f"Active Users: {users_df['MEMBERSHIP_END_DATE'].isna().sum()}")

    st.subheader("Engineer Features")
    features_df = engineer_features(users_df, visits_df)
    st.write(f"Features created: {features_df.shape}")
    st.dataframe(features_df.head())

    # --- Load or Train Model ---
    model_path = Path.cwd().parent / 'output' / 'churn_model.joblib'
    if model_path.exists():
        model = load_model(str(model_path))
        st.success("Trained model loaded successfully!")
    else:
        st.warning("No trained model found. Training a new model now...")
        model, X_test, y_test = train_churn_model(features_df)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        save_model(model, str(model_path))
        st.success("New model trained and saved!")

    st.subheader("Model Performance")
    # For a newly trained model, we'd have X_test and y_test from train_churn_model
    # For a loaded model, we'd need to split features_df to get test set or use a pre-saved test set.
    # For simplicity, re-splitting here for consistent evaluation display.
    _, X_test, y_test = train_churn_model(features_df) # This re-splits, not ideal but for dashboard demo

    results = evaluate_model(model, X_test, y_test)
    st.text("Classification Report:")
    st.code(results['classification_report'])
    st.write(f"ROC-AUC Score: {results['roc_auc_score']:.3f}")

    st.subheader("Feature Importance")
    importance_df = get_feature_importance(model)
    st.dataframe(importance_df.head()) # Show top features

    st.subheader("Churned vs Active Users Comparison")
    comparison_cols = ['visits_per_month', 'days_since_last_visit', 'avg_session_duration_min', 
                       'visit_frequency_trend', 'num_classes_enrolled']
    churned = features_df[features_df['CHURNED'] == 1]
    active = features_df[features_df['CHURNED'] == 0]

    comparison_data = []
    for col in comparison_cols:
        comparison_data.append({
            'Feature': col,
            'Churned (Mean)': churned[col].mean(),
            'Churned (Median)': churned[col].median(),
            'Active (Mean)': active[col].mean(),
            'Active (Median)': active[col].median(),
        })
    st.dataframe(pd.DataFrame(comparison_data).set_index('Feature'))

    st.subheader("At-Risk Active Users")
    risk_df = predict_churn_risk(model, features_df, active_only=True)
    st.write("Risk Distribution (Active Users):")
    st.dataframe(risk_df['risk_level'].value_counts())
    st.write("Top 10 At-Risk Users:")
    st.dataframe(risk_df.head(10))

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_page()
else:
    main_app()


