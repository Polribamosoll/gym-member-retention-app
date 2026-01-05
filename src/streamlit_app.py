import streamlit as st
import pandas as pd
from pathlib import Path
import hashlib
import joblib
import json
import io
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os
from contextlib import contextmanager

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from auxiliar.auxiliar import engineer_features
from src.churn_model import train_churn_model, evaluate_model, get_feature_importance, predict_churn_risk, save_model, load_model, FEATURE_COLUMNS
from app.lang import get_translation, LANGUAGES

# Initialize session state early at module level
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "lang" not in st.session_state:
    st.session_state["lang"] = "en" # Default language
if "loading_states" not in st.session_state:
    st.session_state["loading_states"] = {}

# Translation helper function that can be called from anywhere
def translate(key, default=None, **kwargs):
    """Translate a key using the current session language with optional fallback."""
    current_lang = st.session_state.get("lang", "en")
    text = get_translation(current_lang, key, **kwargs)
    if text.startswith("MISSING_TRANSLATION[") and default is not None:
        return default
    return text

# Generic loading state helpers
def set_loading(key: str, value: bool) -> None:
    st.session_state["loading_states"][key] = value

def is_loading(key: str) -> bool:
    return st.session_state["loading_states"].get(key, False)

def any_loading(*keys: str) -> bool:
    return any(is_loading(k) for k in keys)

@contextmanager
def loading_state(key: str):
    set_loading(key, True)
    try:
        yield
    finally:
        set_loading(key, False)

def save_uploaded_csv(uploaded_file, target_filename: str):
    """Save uploaded CSV to data directory."""
    if uploaded_file is None:
        return False
    data_dir = Path.cwd() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(uploaded_file)
    df.to_csv(data_dir / target_filename, index=False)
    return True

# Reusable footer
def render_footer():
    year = datetime.now().year
    app_name = "Gym Churn Predictor"
    version = os.getenv("APP_VERSION", "v1.0")
    phone = "+34 650998877"
    email = "customer.service@memberpulse.com"
    footer_bg = "#0a0a0a"
    separator = "rgba(255,255,255,0.05)"

    st.markdown(
        f"""
        <style>
        .app-footer {{
            background: {footer_bg};
            padding: 10px 16px;
            border-top: 1px solid {separator};
            color: #9ca3af;
            font-size: 12px;
        }}
        .app-footer .footer-inner {{
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            align-items: center;
            gap: 12px;
        }}
        .app-footer .footer-group {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .app-footer .footer-link {{
            color: #9ca3af;
            text-decoration: none;
        }}
        .app-footer .footer-link:hover {{
            color: #4ade80;
        }}
        .app-footer .muted {{
            color: #9ca3af;
            opacity: 0.9;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="app-footer">
            <div class="footer-inner">
                <div class="footer-group">
                    <span class="muted">Customer Service:</span>
                    <span>{phone}</span>
                    <span>•</span>
                    <a class="footer-link" href="mailto:{email}">{email}</a>
                </div>
                <div class="footer-group">
                    <span>{app_name}</span>
                    <span>•</span>
                    <span>© {year}</span>
                    <span>•</span>
                    <span>{version}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Reusable Loading Indicator --- (New Section)

    if "app_loading_states" not in st.session_state:
        st.session_state.app_loading_states = {}

    def set_app_loading_state(key, is_loading, message_key=None, default_message="Loading..."):
        """Sets the loading state for a specific UI element."""
        if key not in st.session_state.app_loading_states:
            st.session_state.app_loading_states[key] = {"is_loading": False, "message": ""}

        st.session_state.app_loading_states[key]["is_loading"] = is_loading
        if message_key:
            st.session_state.app_loading_states[key]["message"] = translate(message_key, default=default_message)
        else:
            st.session_state.app_loading_states[key]["message"] = default_message
        st.rerun()

    import contextlib
    import time

    @contextlib.contextmanager
    def st_loader(key, default_message_key=None, is_full_width=False, height=None):
        """A context manager for showing a loading indicator in Streamlit.
        Usage:
            with st_loader("my_data_table_loader", default_message_key="loading_data"):  # or is_full_width=True
                # Load your data here
                time.sleep(2)
                st.write("Data Loaded!")
        """
        if key not in st.session_state.app_loading_states:
            st.session_state.app_loading_states[key] = {"is_loading": False, "message": ""}
        
        # Get current loading state and message
        loading_state = st.session_state.app_loading_states[key]["is_loading"]
        loading_message = st.session_state.app_loading_states[key]["message"]

        if not loading_state: # If not already loading, start loading
            set_app_loading_state(key, True, message_key=default_message_key)
            yield # Allow the block to execute and rerun
        else: # If currently loading, display the loader
            if is_full_width:
                # Full-width loading overlay for tables or sections
                with st.container():
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.markdown(f"""
                        <div style='text-align: center; padding: {height or 50}px; background-color: #1a1a1a; border-radius: 10px; margin: 10px 0;'>
                            <h4 style='color: #4ade80; margin-bottom: 10px;'>🔄 {loading_message}</h4>
                            <div style='color: #ffffff;'>Please wait...</div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.spinner("")
            else:
                # Inline spinner for buttons or small content areas
                st.spinner(loading_message)

            try:
                yield # Allow the block to execute (it should trigger a rerun when done)
            finally:
                set_app_loading_state(key, False) # Ensure loading state is reset

    # --- User Management (for demo purposes) ---
USERS_FILE = Path("users.json")

def load_users():
    """Load users from JSON file"""
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    # Default users if file doesn't exist or is corrupted
    return {
        "admin": hashlib.sha256("admin123".encode()).hexdigest()
    }

def save_users(users):
    """Save users to JSON file"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        st.error(f"Error saving users: {e}")

# Initialize users
USERS = load_users()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_password(password, translate_func):
    """Validate password requirements:
    - At least 9 characters long
    - Contains at least one number
    - Contains at least one letter
    - Contains at least one capital letter
    """
    if len(password) < 9 or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password) or not any(char.isupper() for char in password):
        return translate_func("password_requirements")
    return None

def login_page():
    # Set black background for the entire app, soft green titles, and white text
    st.markdown("""
    <style>
    .retention-subtitle {
        color: #4ade80 !important;
    }
    .stApp {
        background-color: #000000;
    }
    .stTitle, .stHeader, .stSubheader {
        color: #4ade80 !important;
    }
    h1, h3, h4, h5, h6 {
        color: #4ade80 !important;
    }
    h2 {
        color: #ffffff !important;
    }
    .stMarkdown, .stText, p, div {
        color: #ffffff !important;
    }
    .stSuccess, .stWarning, .stError, .stInfo {
        color: #ffffff !important;
    }
    .stSuccess > div, .stWarning > div, .stError > div, .stInfo > div {
        color: #ffffff !important;
    }
    div.stButton > button:first-child {
        background-color: transparent;
        color: #4ade80;
        border: 2px solid #4ade80;
        border-radius: 5px;
    }
    div.stButton > button:hover {
        background-color: #4ade80;
        color: #000000;
        border: 2px solid #4ade80;
        border-radius: 5px;
    }
    .stRadio label, .stTextInput label, .stTextArea label {
        color: #ffffff !important;
        font-size: 0.9em !important;
    }
    /* Target radio button options specifically */
    .stRadio div[role="radiogroup"] label {
        color: #ffffff !important;
        font-size: 0.9em !important;
    }
    .css-1lcbmhc .stSelectbox label {
        color: #4ade80 !important;
        font-weight: 600 !important;
    }
    .css-1lcbmhc .stSelectbox div[data-baseweb="select"] {
        background-color: #000000 !important;
        border: 1px solid #4ade80 !important;
        border-radius: 5px !important;
    }
    .css-1lcbmhc .stSelectbox div[data-baseweb="select"] * {
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)
    # Centering the content
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(f"<h1 style='text-align: center; color: #4ade80; font-size: 2.5em;'>Welcome to MemberPulse</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #4ade80; font-size: 1.5em; margin-top: 0.5em; font-weight: bold;' class='retention-subtitle'>Retention, powered by AI.</p>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='text-align: center; color: #ffffff; font-size: 2em;'>{_('login_register')}</h2>", unsafe_allow_html=True)

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
                    # Validate password requirements
                    password_error = validate_password(new_password, _)
                    if password_error:
                        st.error(password_error)
                    elif new_password != confirm_password:
                        st.error(_("passwords_do_not_match"))
                    elif new_username in USERS:
                        st.error(_("username_already_exists"))
                    else:
                        USERS[new_username] = hash_password(new_password)
                        save_users(USERS)  # Save to file
                        st.success(_("account_created_successfully"))
                        st.balloons()
                        st.session_state["show_upload_after_register"] = True
        
        # Upload CSVs after registration (from notebook)
        if st.session_state.get("show_upload_after_register"):
            st.markdown("---")
            st.markdown("### Upload your CSVs to populate the app")
            st.caption("You can generate these files from `notebooks/test_data_generation.ipynb`. Upload `user_information.csv` and `user_visits.csv`.")
            users_upload = st.file_uploader("Upload Users CSV", key="upload_users_csv", type="csv")
            visits_upload = st.file_uploader("Upload Visits CSV", key="upload_visits_csv", type="csv")
            if st.button("Upload CSV files"):
                if users_upload is None or visits_upload is None:
                    st.error("You need to upload both datasets.")
                else:
                    ok_users = save_uploaded_csv(users_upload, "user_information.csv")
                    ok_visits = save_uploaded_csv(visits_upload, "user_visits.csv")
                    if ok_users and ok_visits:
                        st.success("Both CSV files uploaded successfully.")
                    else:
                        st.error("There was a problem saving the files. Please try again.")
            st.caption("Once uploaded, proceed to log in and the app will use these datasets.")
        
        # Adding some spacing at the bottom
        st.markdown("<br><br>", unsafe_allow_html=True)

def main_app():
    # Set black background for the entire app, soft green titles, and white text
    st.markdown("""
    <style>
    .stApp {
        background-color: #000000;
    }
    .stTitle, .stHeader, .stSubheader {
        color: #4ade80 !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #4ade80 !important;
    }
    .stMarkdown, .stText, p, div {
        color: #ffffff !important;
    }
    .metric-light-red {
        color: #FF7F7F !important;
    }
    .stSuccess, .stWarning, .stError, .stInfo {
        color: #ffffff !important;
    }
    .stSuccess > div, .stWarning > div, .stError > div, .stInfo > div {
        color: #ffffff !important;
    }
    .stButton > button {
        background-color: transparent !important;
        color: #4ade80 !important;
        border: 2px solid #4ade80 !important;
        border-radius: 5px !important;
    }
    .stButton > button:hover {
        background-color: #4ade80 !important;
        color: #000000 !important;
        border: 2px solid #4ade80 !important;
        border-radius: 5px !important;
    }
    .css-1lcbmhc .stSelectbox label {
        color: #4ade80 !important;
        font-weight: 600 !important;
    }
    .css-1lcbmhc .stSelectbox div[data-baseweb="select"] {
        background-color: #000000 !important;
        border: 1px solid #4ade80 !important;
        border-radius: 5px !important;
    }
    .css-1lcbmhc .stSelectbox div[data-baseweb="select"] * {
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)


    st.title(_("gym_churn_predictor_dashboard"))
    st.markdown(f"<p style='text-align: center; color: #4ade80; font-size: 1.1em; font-weight: bold;'><i>{_('ai_powered_insights')}</i></p>", unsafe_allow_html=True)

    # --- Load Data ---
    data_dir = Path.cwd() / 'data'
    users_df = pd.read_csv(data_dir / 'user_information.csv', parse_dates=['REGISTRATION_DATE', 'MEMBERSHIP_END_DATE'])
    visits_df = pd.read_csv(data_dir / 'user_visits.csv', parse_dates=['ENTRY_TIME', 'EXIT_TIME'])

    # --- Feature Engineering ---
    features_df = engineer_features(users_df, visits_df)

    # --- Load or Train Model ---
    model_path = Path.cwd().parent / 'output' / 'churn_model.joblib'
    if model_path.exists():
        model = load_model(str(model_path))
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.success(_("trained_model_loaded_successfully"))
        with col2:
            # Get current language with fallback
            current_lang = st.session_state.get("lang", "en")

            if st.button("ℹ️", key="model_info"):
                # Create a modal dialog for the documentation
                @st.dialog(translate("how_the_ai_model_works"))
                def show_model_documentation():
                    # Apply the same dark theme styling to the modal
                    st.markdown("""
                    <style>
                    /* Modal dark theme styling - more specific selectors */
                    .stDialog {
                        background-color: #2a2a2a !important;
                    }
                    .stDialog [data-testid="stDialog"] {
                        background-color: #2a2a2a !important;
                    }
                    /* Target modal content area */
                    [data-testid="stDialog"] .stVerticalBlock {
                        background-color: #2a2a2a !important;
                    }
                    /* Force all modal elements to have dark background */
                    [data-testid="stDialog"],
                    [data-testid="stDialog"] *,
                    [data-testid="stDialog"] .stVerticalBlock,
                    [data-testid="stDialog"] .stMarkdown,
                    [data-testid="stDialog"] .stText {
                        background-color: #2a2a2a !important;
                        color: #ffffff !important;
                    }
                    /* Headers in modal */
                    [data-testid="stDialog"] h1,
                    [data-testid="stDialog"] h2,
                    [data-testid="stDialog"] h3,
                    [data-testid="stDialog"] h4 {
                        color: #4ade80 !important;
                    }
                    /* Success messages in modal */
                    [data-testid="stDialog"] .stSuccess > div {
                        background-color: rgba(74, 222, 128, 0.1) !important;
                        border-color: #4ade80 !important;
                        color: #ffffff !important;
                    }
                    /* Override any default white backgrounds */
                    [data-testid="stDialog"] .stMarkdown,
                    [data-testid="stDialog"] p,
                    [data-testid="stDialog"] div {
                        background-color: transparent !important;
                        color: #ffffff !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)

                    # Title with app's green color
                    st.markdown(f"<h1 style='text-align: center; color: #4ade80; margin-bottom: 30px;'>{ translate('model_explanation_title') }</h1>", unsafe_allow_html=True)

                    # Main explanation text with white color
                    st.markdown(f"<div style='font-size: 18px; line-height: 1.7; margin-bottom: 30px; text-align: center; color: #ffffff;'>{ translate('model_explanation_text') }</div>", unsafe_allow_html=True)

                    # Steps in a more readable format
                    st.markdown(f"## 🔍 **{translate('how_it_works_section')}**")
                    st.markdown("")

                    # Create columns for better layout
                    col1, col2 = st.columns(2)

                    with col1:
                        # Step 1
                        st.markdown(f"### 1️⃣ {translate('data_collection_title')}")
                        st.markdown(f"""
                        <div style='font-size: 16px; margin-bottom: 20px; padding: 15px; background-color: #1a1a1a; border-radius: 8px; border-left: 4px solid #4ade80; min-height: 100px; color: #ffffff;'>
                        {translate('model_step_1')}
                        </div>
                        """, unsafe_allow_html=True)

                        # Step 2
                        st.markdown(f"### 2️⃣ {translate('pattern_recognition_title')}")
                        st.markdown(f"""
                        <div style='font-size: 16px; margin-bottom: 20px; padding: 15px; background-color: #1a1a1a; border-radius: 8px; border-left: 4px solid #4ade80; min-height: 100px; color: #ffffff;'>
                        {translate('model_step_2')}
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        # Step 3
                        st.markdown(f"### 3️⃣ {translate('risk_prediction_title')}")
                        st.markdown(f"""
                        <div style='font-size: 16px; margin-bottom: 20px; padding: 15px; background-color: #1a1a1a; border-radius: 8px; border-left: 4px solid #4ade80; min-height: 100px; color: #ffffff;'>
                        {translate('model_step_3')}
                        </div>
                        """, unsafe_allow_html=True)

                        # Step 4
                        st.markdown(f"### 4️⃣ {translate('actionable_insights_title')}")
                        st.markdown(f"""
                        <div style='font-size: 16px; margin-bottom: 20px; padding: 15px; background-color: #1a1a1a; border-radius: 8px; border-left: 4px solid #4ade80; min-height: 100px; color: #ffffff;'>
                        {translate('model_step_4')}
                        </div>
                        """, unsafe_allow_html=True)

                    # Why it's important
                    st.markdown(f"## 🎯 **{translate('why_this_matters_section')}**")
                    st.success(f"💡 { translate('model_why_important') }")

                show_model_documentation()
    else:
        st.warning(_("no_trained_model_found"))
        model, X_test, y_test = train_churn_model(features_df)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        save_model(model, str(model_path))
        st.success(_("new_model_trained_and_saved"))

    # Predict Churn Risk (moved up to be available for Data Overview and other sections)
    risk_df = predict_churn_risk(model, features_df, active_only=True)

    # 1. Data Overview
    st.subheader(_("data_overview"))
    total_users = len(users_df)
    total_visits = len(visits_df)
    churned_users = users_df['MEMBERSHIP_END_DATE'].notna().sum()
    active_users = users_df['MEMBERSHIP_END_DATE'].isna().sum()
    churn_rate = (churned_users / total_users) * 100 if total_users > 0 else 0

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.markdown(f"""
        <div>
            <div style='font-size: 0.875rem; color: #ffffff; margin-bottom: 0.25rem;'>{_('total_users')}</div>
            <div style='font-size: 1.8rem; font-weight: 600; color: #ffffff; line-height: 1;'>{total_users}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div>
            <div style='font-size: 0.875rem; color: #ffffff; margin-bottom: 0.25rem;'>{_('total_visits')}</div>
            <div style='font-size: 1.8rem; font-weight: 600; color: #ffffff; line-height: 1;'>{total_visits}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div>
            <div style='font-size: 0.875rem; color: #ffffff; margin-bottom: 0.25rem;'>{_('active_users')}</div>
            <div style='font-size: 1.8rem; font-weight: 600; color: #ffffff; line-height: 1;'>{active_users}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div>
            <div style='font-size: 0.875rem; color: #ffffff; margin-bottom: 0.25rem;'>{_('churned_users')}</div>
            <div style='font-size: 1.8rem; font-weight: 600; color: #ffffff; line-height: 1;'>{churned_users}</div>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        # Calculate users at high or medium risk
        users_at_risk_count = risk_df[(risk_df['risk_level'] == 'High') | (risk_df['risk_level'] == 'Medium')].shape[0]
        st.markdown(f"""
        <div>
            <div style='font-size: 0.875rem; color: #ffffff; margin-bottom: 0.25rem;'>{_('users_at_risk')}</div>
            <div style='font-size: 1.8rem; font-weight: 600; line-height: 1;' class='metric-light-red'>{users_at_risk_count}</div>
        </div>
        """, unsafe_allow_html=True)
    with col6:
        st.markdown(f"""
        <div>
            <div style='font-size: 0.875rem; color: #ffffff; margin-bottom: 0.25rem;'>{_('churn_rate')}</div>
            <div style='font-size: 1.8rem; font-weight: 600; line-height: 1;' class='metric-light-red'>{churn_rate:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("") # Add an empty line for separation
    st.write("") # Add another empty line for separation

    # 2. At-Risk Active Users (Donut Plot)
    st.subheader(_("at_risk_active_users"))
    risk_df = predict_churn_risk(model, features_df, active_only=True)


    # Convert value_counts to DataFrame for styling
    risk_distribution = risk_df['risk_level'].value_counts().reset_index()
    risk_distribution.columns = ['Risk Level', 'Count']

    def highlight_risk_distribution(row):
        if row['Risk Level'] == 'High':
            return ['background-color: #FFDDDD'] * len(row)  # Soft red
        elif row['Risk Level'] == 'Medium':
            return ['background-color: #FFEEDD'] * len(row)  # Soft orange
        else:  # Low
            return ['background-color: #DDFFDD'] * len(row)  # Soft green

    # Create color mapping matching app theme
    color_map = {
        'High': '#FF7F7F',  # Light red (matching risk indicators)
        'Medium': '#FFA500',  # Orange (warning)
        'Low': '#4ade80'  # App green (healthy)
    }

    # Create bar chart
    fig = px.pie(
        risk_distribution,
        names='Risk Level',
        values='Count',
        color='Risk Level',
        color_discrete_map=color_map,
        title=None, # Remove title as it's already in the app
        hole=0.5  # Create the donut shape
    )

    # Update layout for donut chart with professional styling
    fig.update_layout(
        showlegend=True,
        legend_title=None,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(color="#e5e7eb")
        ),
        uniformtext_minsize=12,
        uniformtext_mode='hide',
        plot_bgcolor="#0a0a0a",
        paper_bgcolor="#0a0a0a",
        font=dict(color="#e5e7eb"),
        margin=dict(t=0, b=0, l=0, r=0),
    )

    # Update text, hover info, and add subtle outlines
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate="%{label}: %{percent:.1%} (%{value})",
        marker_line_color="#0f0f0f",
        marker_line_width=1.2,
    )

    st.plotly_chart(fig)
    
    # 3. Top 10 At-Risk Users (Table with buttons)
    st.subheader(_("top_10_at_risk_users"))

    # Calculate the number of high-risk users
    num_high_risk_users = len(risk_df[risk_df['risk_level'] == 'High'])
    st.write(_("high_risk_users_message", n=num_high_risk_users))


    # Initialize session state for user_offset and loading flag if not already set
    if 'user_offset' not in st.session_state:
        st.session_state.user_offset = 0
    if 'table_loading' not in st.session_state:
        st.session_state["table_loading"] = False

    # Define a mapping for more readable column names
    column_name_mapping = {
        'CUSTOMER_ID': 'Customer ID',
        'AGE': 'Age',
        'GENDER': 'Gender',
        'MEMBERSHIP_TYPE': 'Membership Type',
        'MONTHLY_PRICE': 'Monthly Price',
        'CONTRACT_LENGTH': 'Contract Length',
        'REGISTRATION_DATE': 'Registration Date',
        'CHURNED': 'Churned',
        'visits_per_month': 'Visits per Month',
        'days_since_last_visit': 'Days Since Last Visit',
        'avg_session_duration_min': 'Avg Session Duration (min)',
        'visit_frequency_trend': 'Visit Frequency Trend',
        'num_classes_enrolled': 'Num Classes Enrolled',
        'churn_risk_score': 'Churn Risk Score',
        'risk_level': 'Risk Level' 
    }
    
    # Inline loader feedback for pagination actions
    loader_placeholder = st.empty()
    if st.session_state.get("table_loading"):
        with loader_placeholder.container():
            st.markdown("""
            <div style='text-align: center; padding: 16px; background-color: #1a1a1a; border-radius: 10px; margin: 6px 0;'>
                <h4 style='color: #4ade80; margin-bottom: 8px;'>🔄 Loading users...</h4>
                <div style='color: #ffffff;'>Please wait a moment.</div>
            </div>
            """, unsafe_allow_html=True)
            with st.spinner(translate("loading_users_message", default="Loading users...")):
                import time
                time.sleep(0.5)
        # Clear loader once data is ready to render
        loader_placeholder.empty()
        st.session_state["table_loading"] = False

    # Get the current slice of users
    current_users_df = risk_df.iloc[st.session_state.user_offset : st.session_state.user_offset + 10]

    # Rename columns and display with no index
    def highlight_risk(row):
        if row['Risk Level'] == 'High':
            return ['background-color: #FFDDDD'] * len(row)  # Soft red
        elif row['Risk Level'] == 'Medium':
            return ['background-color: #FFEEDD'] * len(row)  # Soft orange
        else:
            return [''] * len(row)

    st.dataframe(current_users_df.rename(columns=column_name_mapping).style.apply(highlight_risk, axis=1), hide_index=True)

    # Controls row: back button (left), spacer, download + next (right-aligned)
    col_back, col_spacer, col_download, col_next = st.columns([1, 2, 1, 1])

    with col_back:
        if st.session_state.user_offset > 0:
            back_clicked = st.button(_("back_to_first_10"))
            if back_clicked:
                st.session_state.user_offset = 0
                st.session_state["table_loading"] = True
                st.rerun()

    with col_download:
        export_buffer = io.BytesIO()
        risk_df.rename(columns=column_name_mapping).to_excel(export_buffer, index=False)
        export_buffer.seek(0)
        st.download_button(
            label="Download Excel",
            data=export_buffer,
            file_name="at_risk_users.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )

    with col_next:
        next_disabled = st.session_state.user_offset + 10 >= len(risk_df)
        next_clicked = st.button(_("load_next_10_at_risk_users"), disabled=next_disabled)
        if next_clicked:
            st.session_state.user_offset += 10
            st.session_state["table_loading"] = True
            st.rerun()

    # 4. Feature Importance
    st.subheader(_("feature_importance"))
    importance_df = get_feature_importance(model)

    # Create readable labels for features
    feature_labels = {
        'total_visits': 'Total Visits',
        'visits_per_month': 'Visits per Month',
        'avg_session_duration_min': 'Average Session Duration (min)',
        'days_since_last_visit': 'Days Since Last Visit',
        'avg_days_between_visits': 'Average Days Between Visits',
        'std_days_between_visits': 'Standard Deviation Days Between Visits',
        'visits_last_30_days': 'Visits in Last 30 Days',
        'visits_last_60_days': 'Visits in Last 60 Days',
        'visits_last_90_days': 'Visits in Last 90 Days',
        'pct_peak_hour_visits': 'Percentage Peak Hour Visits',
        'pct_weekend_visits': 'Percentage Weekend Visits',
        'visit_frequency_trend': 'Visit Frequency Trend',
        'membership_duration_months': 'Membership Duration (months)',
        'AGE': 'Age',
        'GENDER': 'Gender'
    }

    # Apply readable labels
    importance_df['feature_label'] = importance_df['feature'].map(feature_labels).fillna(importance_df['feature'])

    # Create the feature importance plot
    fig, ax = plt.subplots(figsize=(12, 10))
    importance_sorted = importance_df.sort_values('importance', ascending=True)
    bars = ax.barh(importance_sorted['feature_label'], importance_sorted['importance'], color='#4ade80')
    ax.set_xlabel('Importance Score', fontsize=12)
    ax.set_title('Feature Importance for Churn Prediction', fontsize=14, fontweight='bold')

    # Add value labels on the bars
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.001, bar.get_y() + bar.get_height()/2,
                f'{width:.3f}', ha='left', va='center', fontsize=10)

    plt.tight_layout()
    st.pyplot(fig)

    # 5. Churned vs Active Users Comparison
    st.subheader(_("churned_vs_active_users_comparison"))

    # Select data
    churned = features_df[features_df['CHURNED'] == 1]
    active = features_df[features_df['CHURNED'] == 0]

    # Define features to compare with readable labels
    feature_comparisons = {
        'visits_per_month': 'Visits per Month',
        'days_since_last_visit': 'Days Since Last Visit',
        'avg_session_duration_min': 'Avg Session Duration (min)',
        'visit_frequency_trend': 'Visit Frequency Trend',
        'num_classes_enrolled': 'Classes Enrolled'
    }

    # Create comparison data for visualization
    comparison_data = []
    for feature_key, feature_name in feature_comparisons.items():
        comparison_data.append({
            'Feature': feature_name,
            'Churned': churned[feature_key].mean(),
            'Active': active[feature_key].mean(),
            'Feature_Key': feature_key
        })

    comparison_df = pd.DataFrame(comparison_data)

    # Create grouped bar chart
    fig, ax = plt.subplots(figsize=(14, 8))

    # Set up the bar positions
    x = np.arange(len(comparison_df))
    width = 0.35

    # Create bars
    churned_bars = ax.bar(x - width/2, comparison_df['Churned'], width,
                          label='Churned Users', color='#FF7F7F', alpha=0.8)
    active_bars = ax.bar(x + width/2, comparison_df['Active'], width,
                         label='Active Users', color='#4ade80', alpha=0.8)

    # Customize the plot
    ax.set_xlabel('', fontsize=12, fontweight='bold')
    ax.set_ylabel('Average Value', fontsize=12, fontweight='bold')
    ax.set_title('', fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(comparison_df['Feature'], rotation=45, ha='right', fontsize=10)
    ax.legend(fontsize=11)

    # Add grid for better readability
    ax.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    def add_value_labels(bars):
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + max(comparison_df[['Churned', 'Active']].max()) * 0.02,
                    f'{height:.1f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

    add_value_labels(churned_bars)
    add_value_labels(active_bars)

    plt.tight_layout()
    st.pyplot(fig)

    summary_data = []
    for feature_key, feature_name in feature_comparisons.items():
        churned_mean = churned[feature_key].mean()
        active_mean = active[feature_key].mean()
        difference = ((churned_mean - active_mean) / active_mean * 100) if active_mean != 0 else 0

        summary_data.append({
            'Feature': feature_name,
            'Churned (Mean)': churned_mean,
            'Active (Mean)': active_mean,
            'Difference (%)': difference
        })

    summary_df = pd.DataFrame(summary_data).set_index('Feature')

    # Apply app-themed styling to the summary table
    def diff_cell_style(val):
        if val > 0:
            return 'background-color: rgba(74, 222, 128, 0.18); color: #000000; font-weight: 700;'
        if val < 0:
            return 'background-color: rgba(255, 127, 127, 0.18); color: #000000; font-weight: 700;'
        return 'color: #000000; font-weight: 700;'

    styled_summary = (
        summary_df.style
        .format({
            'Churned (Mean)': "{:.2f}",
            'Active (Mean)': "{:.2f}",
            'Difference (%)': "{:+.1f}%"
        })
        .set_table_styles([
            {'selector': 'table', 'props': [
                ('background-color', '#0a0a0a'),
                ('color', '#e5e7eb'),
                ('border', '1px solid #1f1f1f'),
                ('border-collapse', 'collapse')
            ]},
            {'selector': 'thead th', 'props': [
                ('background', '#cce6ff'),
                ('color', '#000000'),
                ('font-weight', 'bold'),
                ('border-bottom', '1px solid #4ade80'),
                ('padding', '10px')
            ]},
            {'selector': 'tbody td', 'props': [
                ('background-color', '#0f0f0f'),
                ('color', '#e5e7eb'),
                ('border-bottom', '1px solid #1f1f1f'),
                ('padding', '8px 10px')
            ]},
            {'selector': 'tbody tr:nth-child(even) td', 'props': [
                ('background-color', '#111111')
            ]},
        ])
        .applymap(diff_cell_style, subset=pd.IndexSlice[:, ['Difference (%)']])
    )

    st.dataframe(styled_summary, use_container_width=True)

    # Users evolution (last 12 months)
    st.subheader("Users evolution")
    today = pd.Timestamp.today().normalize()
    start_month = (today - pd.DateOffset(months=11)).replace(day=1)
    months_range = pd.date_range(start_month, today, freq='MS')

    evolution_rows = []
    for month_start in months_range:
        month_end = month_start + pd.offsets.MonthEnd(1)
        label = month_start.strftime("%Y-%m")
        new_count = users_df[users_df['REGISTRATION_DATE'].dt.to_period('M') == month_start.to_period('M')].shape[0]
        churned_count = users_df[
            users_df['MEMBERSHIP_END_DATE'].notna() &
            (users_df['MEMBERSHIP_END_DATE'].dt.to_period('M') == month_start.to_period('M'))
        ].shape[0]
        active_count = users_df[
            (users_df['REGISTRATION_DATE'] <= month_end) &
            (
                users_df['MEMBERSHIP_END_DATE'].isna() |
                (users_df['MEMBERSHIP_END_DATE'] > month_end)
            )
        ].shape[0]
        evolution_rows.append(
            {"Month": label, "Active": active_count, "New": new_count, "Churned": churned_count}
        )

    evolution_df = pd.DataFrame(evolution_rows)
    # Users evolution (last 12 months) - no title
    fig_evo = px.bar(
        evolution_df,
        x="Month",
        y=["Active", "New", "Churned"],
        barmode="group",
        title="",
        color_discrete_map={
            "Active": "#4ade80",
            "New": "#60a5fa",
            "Churned": "#f472b6",
        },
    )
    fig_evo.update_traces(
        marker_line_width=0.5,
        marker_line_color="#0f0f0f",
        hovertemplate="%{x}: %{y}",
        texttemplate="%{y}",
        textposition="outside",
        cliponaxis=False,
    )
    fig_evo.update_layout(
        xaxis_title="",
        yaxis_title="Users",
        xaxis_tickangle=-45,
        bargap=0.15,
        bargroupgap=0.1,
        plot_bgcolor="#0a0a0a",
        paper_bgcolor="#0a0a0a",
        xaxis=dict(gridcolor="#2a2a2a", zeroline=False),
        yaxis=dict(gridcolor="#2a2a2a", zeroline=False),
    )
    st.plotly_chart(fig_evo, use_container_width=True)

    # Activity heatmap and time series (open hours buckets, last 2 months)
    st.markdown(f"#### {translate('calendar_activity_title', default='Calendar Activity')}")
    heat_start = (today - pd.DateOffset(months=2)).normalize()
    visits_recent = visits_df[visits_df['ENTRY_TIME'] >= heat_start].copy()
    if not visits_recent.empty:
        max_date = visits_recent['ENTRY_TIME'].max().normalize()
    else:
        max_date = today
    open_start_hour = 8   # gym opens at 08:00
    open_end_hour = 22    # gym closes at 22:00
    bucket_size = 2       # 2-hour buckets make the plot denser and focused
    if not visits_recent.empty:
        visits_recent['date'] = visits_recent['ENTRY_TIME'].dt.date
        visits_recent['hour'] = visits_recent['ENTRY_TIME'].dt.hour

        visits_recent = visits_recent[
            (visits_recent['hour'] >= open_start_hour) & (visits_recent['hour'] < open_end_hour)
        ].copy()

        visits_recent['bucket_start'] = ((visits_recent['hour'] - open_start_hour) // bucket_size) * bucket_size + open_start_hour
        visits_recent['bucket_label'] = visits_recent['bucket_start'].astype(int).astype(str).str.zfill(2) + ":00"

        heat_counts = (
            visits_recent
            .groupby(['date', 'bucket_label'])
            .size()
            .reset_index(name='count')
        )

        all_buckets = [f"{str(b).zfill(2)}:00" for b in range(open_start_hour, open_end_hour, bucket_size)]
        all_dates = pd.date_range(heat_start, max_date, freq='D').date
        full_index = pd.MultiIndex.from_product([all_dates, all_buckets], names=['date', 'bucket_label'])
        heat_counts = heat_counts.set_index(['date', 'bucket_label']).reindex(full_index, fill_value=0).reset_index()

        heat_pivot = heat_counts.pivot(index='date', columns='bucket_label', values='count')
        heat_pivot = heat_pivot.sort_index(ascending=False)

        st.markdown(f"**{translate('activity_heatmap_subtitle', default='Activity heatmap')}**")

        fig_heat = px.imshow(
            heat_pivot,
            color_continuous_scale="YlOrRd",
            aspect="auto",
            labels=dict(color="Entries"),
        )
        fig_heat.update_layout(
            xaxis_title=f"{bucket_size}-hour bucket (open hours)",
            yaxis_title="Date",
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        ts_counts = (
            heat_counts
            .groupby('date')['count']
            .sum()
            .reset_index()
            .sort_values('date')
        )
        ts_counts['date'] = pd.to_datetime(ts_counts['date'])
        ts_counts['is_weekend'] = ts_counts['date'].dt.dayofweek >= 5
        ts_counts['color'] = ts_counts['is_weekend'].map({True: "#f472b6", False: "#4ade80"})
        st.markdown(f"**{translate('activity_time_series_subtitle', default='Activity time series')}**")

        fig_ts = px.bar(
            ts_counts,
            x='date',
            y='count',
            labels={'date': 'Date', 'count': 'Entries'},
            color='color',
            color_discrete_map="identity",
        )
        fig_ts.update_traces(
            showlegend=False,
            marker_line_width=0.5,
            marker_line_color="#0f0f0f",
            hovertemplate="%{x|%Y-%m-%d}: %{y}",
            texttemplate="%{y}",
            textposition="outside",
            cliponaxis=False,
        )
        fig_ts.update_layout(
            xaxis_title="",
            yaxis_title="Entries",
            xaxis_tickangle=-45,
            plot_bgcolor="#0a0a0a",
            paper_bgcolor="#0a0a0a",
            xaxis=dict(gridcolor="#2a2a2a", zeroline=False),
            yaxis=dict(gridcolor="#2a2a2a", zeroline=False),
        )
        st.plotly_chart(fig_ts, use_container_width=True)
    else:
        st.info("No visits in the last 2 months to display.")

    # Churned compared to time since registration
    st.subheader(translate("churn_vs_time_section", default="Churned compared to time since registration"))
    if users_df.empty or 'REGISTRATION_DATE' not in users_df.columns:
        st.info(translate("no_data_churn_vs_time", default="No data available to plot churn vs time since registration."))
    else:
        churn_curve_df = users_df.copy()
        if 'CHURNED' not in churn_curve_df.columns:
            churn_curve_df['CHURNED'] = churn_curve_df['MEMBERSHIP_END_DATE'].notna().astype(int)
        else:
            churn_curve_df['CHURNED'] = churn_curve_df['CHURNED'].astype(int)

        today_ts = pd.Timestamp.today().normalize()
        churn_curve_df['TENURE_MONTH'] = ((today_ts - churn_curve_df['REGISTRATION_DATE']).dt.days / 30.4).clip(lower=0)
        churn_curve_df['TENURE_MONTH'] = churn_curve_df['TENURE_MONTH'].round().astype(int)
        max_month = int(churn_curve_df['TENURE_MONTH'].max()) if not churn_curve_df.empty else 0
        month_index = pd.Index(range(0, max_month + 1))

        churn_curve = (
            churn_curve_df.groupby('TENURE_MONTH')['CHURNED']
            .mean()
            .mul(100)
            .reindex(month_index)
            .reset_index()
        )
        churn_curve.columns = ["Months since registration", "Churn Rate (%)"]

        fig_curve = px.line(
            churn_curve,
            x="Months since registration",
            y="Churn Rate (%)",
            markers=True,
            labels={
                "Months since registration": translate("time_since_registration_axis", default="Time since registration (months)"),
                "Churn Rate (%)": translate("churn_rate_axis", default="Churn rate (%)"),
            },
        )
        # Base line and points in black
        fig_curve.update_traces(line_color="#000000", marker_color="#000000")
        # Add linear trend line in green (only if at least 2 valid points)
        churn_clean = churn_curve.dropna(subset=["Churn Rate (%)"])
        if len(churn_clean) >= 2:
            x_vals = churn_clean["Months since registration"].to_numpy()
            y_vals = churn_clean["Churn Rate (%)"].to_numpy()
            coeffs = np.polyfit(x_vals, y_vals, 1)
            churn_curve["trend"] = coeffs[0] * churn_curve["Months since registration"] + coeffs[1]
            fig_curve.add_scatter(
                x=churn_curve["Months since registration"],
                y=churn_curve["trend"],
                mode="lines",
                name="Trend",
                line=dict(color="#4ade80", width=3),
                showlegend=False,
            )
        fig_curve.update_layout(
            xaxis_title=translate("time_since_registration_axis", default="Time since registration (months)"),
            yaxis_title=translate("churn_rate_axis", default="Churn rate (%)"),
            hovermode="x unified",
        )
        st.plotly_chart(fig_curve, use_container_width=True)

    # Group Segmentation
    st.subheader("Group Segmentation")

    def plot_churn_rate(df, group_col, title, color_map=None, category_order=None, y_label=""):
        if df.empty or group_col not in df.columns:
            st.info(f"No data available for {title}.")
            return
        grouped = (
            df.groupby(group_col)['CHURNED']
            .mean()
            .mul(100)
            .reset_index()
            .rename(columns={'CHURNED': 'Churn Rate (%)'})
        )
        fig = px.bar(
            grouped,
            y=group_col,
            x='Churn Rate (%)',
            color=group_col if color_map else None,
            color_discrete_map=color_map if color_map else None,
            category_orders={group_col: category_order} if category_order else None,
            orientation="h",
        )
        fig.update_traces(
            marker_line_width=0.5,
            marker_line_color="#0f0f0f",
            hovertemplate="%{y}: %{x:.1f}%",
            texttemplate="%{x:.1f}%",
            textposition="outside",
            cliponaxis=False,
        )
        fig.update_layout(
            xaxis_title="Churn Rate (%)",
            yaxis_title=y_label,
            bargap=0.2,
            bargroupgap=0.15,
            showlegend=False,
            yaxis_categoryorder='array' if category_order else None,
            yaxis_categoryarray=category_order if category_order else None,
            plot_bgcolor="#0a0a0a",
            paper_bgcolor="#0a0a0a",
            xaxis=dict(gridcolor="#2a2a2a", zeroline=False),
            yaxis=dict(gridcolor="#2a2a2a", zeroline=False),
        )
        if not color_map:
            fig.update_traces(marker_color="#4ade80")
        st.markdown(f"**{title}**")
        st.plotly_chart(fig, use_container_width=True)

    # Base dataframe for churn segmentation
    seg_df = users_df.copy()
    if 'CHURNED' not in seg_df.columns:
        seg_df['CHURNED'] = seg_df['MEMBERSHIP_END_DATE'].notna().astype(int)
    else:
        seg_df['CHURNED'] = seg_df['CHURNED'].astype(int)

    # Churn rate by gender
    gender_map = {"F": "#60a5fa", "M": "#4ade80"}
    seg_df['GENDER_LABEL'] = seg_df['GENDER'].map({"F": "Female", "M": "Male"}).fillna(seg_df['GENDER'])
    plot_churn_rate(seg_df, 'GENDER_LABEL', "Churn rate by gender", color_map={"Female": "#60a5fa", "Male": "#4ade80"})

    # Churn rate by number of enrolled classes (0–1, 2–3, 4+)
    class_cols = [c for c in ['ZUMBA', 'BODY_PUMP', 'PILATES', 'SPINNING'] if c in seg_df.columns]
    if class_cols:
        seg_df['NUM_CLASSES'] = seg_df[class_cols].sum(axis=1)
        def classes_bin(n):
            if n <= 1:
                return "0-1"
            elif n <= 3:
                return "2-3"
            return "4+"
        seg_df['CLASSES_BIN'] = seg_df['NUM_CLASSES'].apply(classes_bin)
        classes_map = {"0-1": "#4ade80", "2-3": "#60a5fa", "4+": "#f472b6"}
        plot_churn_rate(
            seg_df,
            'CLASSES_BIN',
            "Churn rate by number of enrolled classes",
            category_order=["0-1", "2-3", "4+"],
            color_map=classes_map,
            y_label="Enrolled classes",
        )

    # Churn rate by tenure buckets (0–1, 1–3, 3–6, 6+ months)
    today_ts = pd.Timestamp.today().normalize()
    seg_df['TENURE_MONTHS'] = (today_ts - seg_df['REGISTRATION_DATE']).dt.days / 30.4
    def tenure_bin(m):
        if m <= 1:
            return "0-1"
        elif m <= 3:
            return "1-3"
        elif m <= 6:
            return "3-6"
        return "6+"
    seg_df['TENURE_BIN'] = seg_df['TENURE_MONTHS'].apply(tenure_bin)
    tenure_map = {"0-1": "#4ade80", "1-3": "#60a5fa", "3-6": "#f59e0b", "6+": "#f472b6"}
    plot_churn_rate(
        seg_df,
        'TENURE_BIN',
        "Churn rate by tenure",
        category_order=["0-1", "1-3", "3-6", "6+"],
        color_map=tenure_map,
        y_label="Time since registration",
    )

    # Churn rate by age bins
    age_bins = [0, 25, 35, 50, 120]
    age_labels = ["0-25", "25-35", "35-50", "50+"]
    seg_df['AGE_BIN'] = pd.cut(seg_df['AGE'], bins=age_bins, labels=age_labels, right=False)
    age_map = {"0-25": "#4ade80", "25-35": "#60a5fa", "35-50": "#f59e0b", "50+": "#f472b6"}
    plot_churn_rate(
        seg_df,
        'AGE_BIN',
        "Churn rate by age",
        category_order=age_labels,
        color_map=age_map,
        y_label="Age",
    )

    # Footer spacing and render
    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    render_footer()


# Language selector with custom styling
with st.sidebar:
    # Logo at the top of sidebar
    st.image("assets/Logo.png", width=500, use_container_width=False)

    st.markdown("""
    <style>
    /* AGGRESSIVE: Force ALL sidebar content to be green and bold */
    [data-testid="stSidebar"] {
        background-color: #1a1a1a !important;
        border-right: 3px solid #4ade80 !important;
    }

    /* Force everything in sidebar to be green and bold */
    [data-testid="stSidebar"] * {
        color: #4ade80 !important;
        font-weight: bold !important;
    }

    /* Button styling */
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
        background-color: transparent !important;
        border: 2px solid #4ade80 !important;
        border-radius: 5px !important;
    }

    /* Dropdown styling */
    div[data-baseweb="popover"] {
        background-color: #1a1a1a !important;
        border: 1px solid #4ade80 !important;
        border-radius: 5px !important;
    }

    /* Force ALL dropdown content to be green and bold */
    div[data-baseweb="popover"] *,
    li[role="option"] *,
    div[role="option"] * {
        color: #4ade80 !important;
        background-color: #1a1a1a !important;
        font-weight: bold !important;
    }

    /* Hover states */
    li[role="option"]:hover,
    div[role="option"]:hover,
    li[role="option"]:hover *,
    div[role="option"]:hover * {
        background-color: #4ade80 !important;
        color: #000000 !important;
    }

    /* Cool Table Styling */
    .stDataFrame {
        background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 50%, #1a1a1a 100%) !important;
        border-radius: 10px !important;
        border: 2px solid #4ade80 !important;
        box-shadow: 0 8px 32px rgba(74, 222, 128, 0.1) !important;
        overflow: hidden !important;
    }

    .stDataFrame > div {
        background: transparent !important;
    }

    /* Table headers */
    .stDataFrame thead th {
        background: linear-gradient(90deg, #4ade80 0%, #22c55e 100%) !important;
        color: #000000 !important;
        font-weight: bold !important;
        border: none !important;
        padding: 12px !important;
        text-align: center !important;
    }

    /* Table cells */
    .stDataFrame tbody td {
        color: #ffffff !important;
        border-bottom: 1px solid #4ade80 !important;
        padding: 10px !important;
        text-align: center !important;
    }

    /* Alternating row colors */
    .stDataFrame tbody tr:nth-child(even) {
        background-color: rgba(74, 222, 128, 0.05) !important;
    }

    .stDataFrame tbody tr:nth-child(odd) {
        background-color: rgba(74, 222, 128, 0.02) !important;
    }

    /* Hover effect for rows */
    .stDataFrame tbody tr:hover {
        background-color: rgba(74, 222, 128, 0.1) !important;
        transform: scale(1.01) !important;
        transition: all 0.2s ease !important;
    }

    /* Special styling for highlighted risk rows */
    .stDataFrame tbody tr[data-row-highlight="high"] {
        background: linear-gradient(90deg, rgba(255, 100, 100, 0.1) 0%, rgba(255, 50, 50, 0.1) 100%) !important;
        border-left: 4px solid #ff4444 !important;
    }

    .stDataFrame tbody tr[data-row-highlight="medium"] {
        background: linear-gradient(90deg, rgba(255, 150, 50, 0.1) 0%, rgba(255, 100, 50, 0.1) 100%) !important;
        border-left: 4px solid #ff8800 !important;
    }

    /* Debug: Add visible markers */
    div[data-testid="stVerticalBlock"] div[data-testid="stDataFrame"]:nth-of-type(2) .stDataFrame {
        border: 3px solid #ff0000 !important; /* Red border for debugging */
    }
    div[data-testid="stVerticalBlock"] div[data-testid="stDataFrame"]:nth-of-type(3) .stDataFrame {
        border: 3px solid #00ff00 !important; /* Green border for debugging */
    }

    </style>
    """, unsafe_allow_html=True)

    # Language selector
    selected_lang_name = st.selectbox("Language", options=list(LANGUAGES.values()), index=list(LANGUAGES.keys()).index(st.session_state["lang"]))

    # Update session state if language changes
    selected_lang_code = [code for code, name in LANGUAGES.items() if name == selected_lang_name][0]
    if selected_lang_code != st.session_state["lang"]:
        st.session_state["lang"] = selected_lang_code
        st.rerun()

    # Define translation function
    _ = lambda key, **kwargs: get_translation(st.session_state["lang"], key, **kwargs)

if not st.session_state["logged_in"]:
    login_page()
else:
    main_app()
