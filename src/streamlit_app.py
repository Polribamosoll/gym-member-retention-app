import streamlit as st
import pandas as pd
from pathlib import Path
import hashlib
import joblib
import json
import plotly.express as px

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from auxiliar.auxiliar import engineer_features
from src.churn_model import train_churn_model, evaluate_model, get_feature_importance, predict_churn_risk, save_model, load_model, FEATURE_COLUMNS
from app.lang import get_translation, LANGUAGES

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
        
        # Adding some spacing at the bottom
        st.markdown("<br><br>", unsafe_allow_html=True)

def main_app():
    st.title(_("gym_churn_predictor_dashboard"))
    st.markdown(f"<p style=\'text-align: center; color: #B3D4FF; font-size: 1.1em; font-weight: bold;\'><i>{_('ai_powered_insights')}</i></p>", unsafe_allow_html=True)
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
        st.markdown(f"""
        <div style='text-align: center; padding: 0.25rem 0 1rem 0;'>
            <div style='font-size: 0.875rem; color: rgb(107, 114, 128); margin-bottom: 0.25rem;'>{_('churn_rate')}</div>
            <div style='font-size: 2.25rem; font-weight: 600; color: {color}; line-height: 1;'>{churn_rate:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

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
    risk_distribution.columns = ['Risk Level', 'Count']

    def highlight_risk_distribution(row):
        if row['Risk Level'] == 'High':
            return ['background-color: #FFDDDD'] * len(row)  # Soft red
        elif row['Risk Level'] == 'Medium':
            return ['background-color: #FFEEDD'] * len(row)  # Soft orange
        else:  # Low
            return ['background-color: #DDFFDD'] * len(row)  # Soft green

    # Create more vibrant color mapping for bar chart
    color_map = {
        'High': '#FF4444',  # Vibrant red
        'Medium': '#FF8800',  # Vibrant orange
        'Low': '#44AA44'  # Vibrant green
    }

    # Create bar chart
    fig = px.bar(
        risk_distribution,
        x='Risk Level',
        y='Count',
        color='Risk Level',
        color_discrete_map=color_map,
        title='Risk Distribution (Active Users)',
        text='Count'  # Add count labels above bars
    )

    # Center the bars and update layout
    fig.update_layout(
        showlegend=False,
        xaxis={'categoryorder': 'array', 'categoryarray': ['High', 'Medium', 'Low']},
        bargap=0.3  # Add gap between bars for better centering
    )

    # Update text position to above the bars
    fig.update_traces(textposition='outside')

    st.plotly_chart(fig)
    
    st.write(_("top_10_at_risk_users"))

    # Initialize session state for user_offset if not already set
    if 'user_offset' not in st.session_state:
        st.session_state.user_offset = 0

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

    # Buttons for pagination
    col_buttons1, col_buttons2 = st.columns([1, 1])

    with col_buttons1:
        if st.session_state.user_offset > 0:
            if st.button(_("back_to_first_10")):
                st.session_state.user_offset = 0
                st.rerun()

    with col_buttons2:
        if st.session_state.user_offset + 10 < len(risk_df):
            if st.button(_("load_next_10_at_risk_users")):
                st.session_state.user_offset += 10
                st.rerun()

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

if not st.session_state["logged_in"]:
    login_page()
else:
    main_app()
