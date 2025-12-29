import streamlit as st
import pandas as pd
from pathlib import Path
import hashlib
import joblib
import json
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np

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
        st.success(_("trained_model_loaded_successfully"))
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

    # Create more vibrant color mapping for bar chart
    color_map = {
        'High': '#FF4444',  # Vibrant red
        'Medium': '#FF8800',  # Vibrant orange
        'Low': '#44AA44'  # Vibrant green
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

    # Update layout for donut chart
    fig.update_layout(
        showlegend=True,  # Show legend for pie chart
        uniformtext_minsize=12, 
        uniformtext_mode='hide'
    )

    # Update text and hover info for pie chart
    fig.update_traces(textposition='inside', textinfo='percent+label', hoverinfo='label+percent+value')

    st.plotly_chart(fig)
    
    # 3. Top 10 At-Risk Users (Table with buttons)
    st.subheader(_("top_10_at_risk_users"))

    # Calculate the number of high-risk users
    num_high_risk_users = len(risk_df[risk_df['risk_level'] == 'High'])
    st.write(_("high_risk_users_message", n=num_high_risk_users))


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
    bars = ax.barh(importance_sorted['feature_label'], importance_sorted['importance'], color='steelblue')
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
                          label='Churned Users', color='#FF6B6B', alpha=0.8)
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
                    f'{height:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    add_value_labels(churned_bars)
    add_value_labels(active_bars)

    plt.tight_layout()
    st.pyplot(fig)

    # Add summary statistics table below the chart
    st.markdown("### Summary Statistics")
    summary_data = []
    for feature_key, feature_name in feature_comparisons.items():
        churned_mean = churned[feature_key].mean()
        active_mean = active[feature_key].mean()
        difference = ((churned_mean - active_mean) / active_mean * 100) if active_mean != 0 else 0

        summary_data.append({
            'Feature': feature_name,
            'Churned (Mean)': f"{churned_mean:.2f}",
            'Active (Mean)': f"{active_mean:.2f}",
            'Difference (%)': f"{difference:+.1f}%"
        })

    st.dataframe(pd.DataFrame(summary_data).set_index('Feature'), use_container_width=True)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "lang" not in st.session_state:
    st.session_state["lang"] = "en" # Default language

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
    selected_lang_name = st.selectbox("Language", options=list(LANGUAGES.values()), index=list(LANGUAGES.keys()).index(st.session_state["lang"]))

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
