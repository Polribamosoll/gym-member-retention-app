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
from app.lang import get_translation, LANGUAGES

# --- User Management (for demo purposes) ---
USERS = {
    "admin": hashlib.sha256("admin123".encode()).hexdigest()
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_page():
    st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #B3D4FF;
        color: black;
    }
    div.stButton > button:hover {
        background-color: #84B0F5;
        color: black;
    }
    </style>
    """, unsafe_allow_html=True)
    # Centering the content
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(f"<h1 style='text-align: center; color: #6495ED; font-size: 3.5em;'>{_('gym_churn_predictor')}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center; color: #4b5563; font-size: 2em;'>{_('login_register')}</h2>", unsafe_allow_html=True)

        login_register_container = st.container()
        with login_register_container:
            choice = st.radio(_("login_register"), [_("login"), _("register")], horizontal=True, label_visibility="collapsed")
            
            if choice == _("login"):
                st.markdown("---")
                username = st.text_input(f"**{_('username')}**")
                password = st.text_input(f"**{_('password')}**", type="password")
                
                if st.button(_("login"), use_container_width=True):
                    hashed_password = hash_password(password)
                    if username in USERS and USERS[username] == hashed_password:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = username
                        st.success(f"{_('welcome', username=username)}")
                        st.rerun()
                    else:
                        st.error(_("invalid_username_or_password"))
            
            elif choice == _("register"):
                st.markdown("---")
                st.subheader(_("create_a_new_account"))
                new_username = st.text_input(f"**{_('new_username')}**")
                new_password = st.text_input(f"**{_('new_password')}**", type="password")
                confirm_password = st.text_input(f"**{_('confirm_password')}**", type="password")
                
                if st.button(_("register"), use_container_width=True):
                    if new_password != confirm_password:
                        st.error(_("passwords_do_not_match"))
                    elif new_username in USERS:
                        st.error(_("username_already_exists"))
                    else:
                        USERS[new_username] = hash_password(new_password)
                        st.success(_("account_created_successfully"))
                        st.balloons()
        
        # Adding some spacing at the bottom
        st.markdown("<br><br>", unsafe_allow_html=True)

def main_app():
    st.title(_("gym_churn_predictor_dashboard"))
    st.markdown(f"<p style='text-align: center; color: #B3D4FF; font-size: 1.1em;'><i>{_('ai_powered_insights')}</i></p>", unsafe_allow_html=True)
    st.write(f"{_('welcome', username=st.session_state['username'])}")

    # --- Load Data ---
    data_dir = Path.cwd() / 'data'
    users_df = pd.read_csv(data_dir / 'user_information.csv', parse_dates=['REGISTRATION_DATE', 'MEMBERSHIP_END_DATE'])
    visits_df = pd.read_csv(data_dir / 'user_visits.csv', parse_dates=['ENTRY_TIME', 'EXIT_TIME'])

    st.subheader(_("data_overview"))
    total_users = len(users_df)
    total_visits = len(visits_df)
    churned_users = users_df['MEMBERSHIP_END_DATE'].notna().sum()
    active_users = users_df['MEMBERSHIP_END_DATE'].isna().sum()
    churn_rate = (churned_users / total_users) * 100 if total_users > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(label=_("total_users"), value=total_users)
    with col2:
        st.metric(label=_("total_visits"), value=total_visits)
    with col3:
        st.metric(label=_("active_users"), value=active_users)
    with col4:
        st.metric(label=_("churned_users"), value=churned_users)
    with col5:
        color = "green"
        if churn_rate >= 10:
            color = "red"
        elif churn_rate >= 5:
            color = "orange"
        st.markdown(f"<p style='text-align: center; color: black; font-size: 1em; margin-bottom: 0px;'>{_('churn_rate')}</p><h2 style='text-align: center; color: {color}; font-size: 2em; margin-top: 0px;'>{churn_rate:.2f}%</h2>", unsafe_allow_html=True)

    st.subheader(_("features_used_to_predict_churn"))
    features_df = engineer_features(users_df, visits_df)
    st.write(f"{_('features_created', shape=features_df.shape)}")
    st.dataframe(features_df.head())

    # --- Load or Train Model ---
    model_path = Path.cwd().parent / 'output' / 'churn_model.joblib'
    if model_path.exists():
        model = load_model(str(model_path))
        st.success(_("trained_model_loaded_successfully"))
    else:
        st.warning(_("no_trained_model_found"))
        model, X_test, y_test = train_churn_model(features_df)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        save_model(model, str(model_path))
        st.success(_("new_model_trained_and_saved"))


    st.subheader(_("feature_importance"))
    importance_df = get_feature_importance(model)
    st.dataframe(importance_df.head()) # Show top features

    st.subheader(_("churned_vs_active_users_comparison"))
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

    st.subheader(_("at_risk_active_users"))
    risk_df = predict_churn_risk(model, features_df, active_only=True)
    st.write(_("risk_distribution_active_users"))
    
    # Convert value_counts to DataFrame for styling
    risk_distribution = risk_df['risk_level'].value_counts().reset_index()
    risk_distribution.columns = [risk_level_col_name, 'Count']

    def highlight_risk_distribution(row):
        if row[risk_level_col_name] == _('risk_level_high'):
            return ['background-color: #FFDDDD'] * len(row)  # Soft red
        elif row[risk_level_col_name] == _('risk_level_medium'):
            return ['background-color: #FFEEDD'] * len(row)  # Soft orange
        else:  # Low
            return ['background-color: #DDFFDD'] * len(row)  # Soft green

    st.dataframe(risk_distribution.style.apply(highlight_risk_distribution, axis=1), hide_index=True)
    
    st.write(_("top_10_at_risk_users"))
    # Define a mapping for more readable column names
    column_name_mapping = {
        'CUSTOMER_ID': _('customer_id'),
        'AGE': _('age'),
        'GENDER': _('gender'),
        'MEMBERSHIP_TYPE': _('membership_type'),
        'MONTHLY_PRICE': _('monthly_price'),
        'CONTRACT_LENGTH': _('contract_length'),
        'REGISTRATION_DATE': _('registration_date'),
        'CHURNED': _('churned'),
        'visits_per_month': _('visits_per_month'),
        'days_since_last_visit': _('days_since_last_visit'),
        'avg_session_duration_min': _('avg_session_duration_min'),
        'visit_frequency_trend': _('visit_frequency_trend'),
        'num_classes_enrolled': _('num_classes_enrolled'),
        'churn_risk_score': _('churn_risk_score'),
        'risk_level': _('risk_level')
    }
    
    # Rename columns and display with no index
    def highlight_risk(row):
        if row[risk_level_col_name] == _('risk_level_high'):
            return ['background-color: #FFDDDD'] * len(row)  # Soft red
        elif row[risk_level_col_name] == _('risk_level_medium'):
            return ['background-color: #FFEEDD'] * len(row)  # Soft orange
        else:
            return [''] * len(row)

    st.dataframe(risk_df.head(10).rename(columns=column_name_mapping).style.apply(highlight_risk, axis=1), hide_index=True)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "lang" not in st.session_state:
    st.session_state["lang"] = "en" # Default language

# Language selector
selected_lang_name = st.sidebar.selectbox("Language", options=list(LANGUAGES.values()), index=list(LANGUAGES.keys()).index(st.session_state["lang"]))

# Update session state if language changes
selected_lang_code = [code for code, name in LANGUAGES.items() if name == selected_lang_name][0]
if selected_lang_code != st.session_state["lang"]:
    st.session_state["lang"] = selected_lang_code
    st.rerun()

_ = lambda key, **kwargs: get_translation(st.session_state["lang"], key, **kwargs)
risk_level_col_name = _('risk_level')

if not st.session_state["logged_in"]:
    login_page()
else:
    main_app()
