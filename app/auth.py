"""
Authentication module for Anticipa Streamlit app

Uses Supabase with custom auth table for authentication.
Passwords are hashed with bcrypt (industry standard).
"""

import streamlit as st
import os
from pathlib import Path
from typing import Optional, Dict
import bcrypt
from supabase import create_client, Client
from dotenv import load_dotenv
from theme import PRIMARY_COLOR, ACCENT_COLOR, TEXT_LIGHT, BORDER_COLOR, ERROR_COLOR, WARNING_COLOR
from app_config import ALLOW_SIGNUP, DEMO_USERNAME, DEMO_PASSWORD
from logo_utils import get_logo_html

# Load environment variables from .env file
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)


class AuthManager:
    """
    Manages user authentication using Supabase.
    
    Uses custom auth table (configured via SUPABASE_SCHEMA.AUTH_TABLE) with bcrypt password hashing.
    Table structure:
    - id: SERIAL PRIMARY KEY
    - username: VARCHAR(50) UNIQUE NOT NULL
    - password_hash: VARCHAR(255) NOT NULL (bcrypt)
    - name: VARCHAR(100) NOT NULL
    - role: VARCHAR(20) NOT NULL DEFAULT 'user'
    - created_at: TIMESTAMP DEFAULT NOW()
    - updated_at: TIMESTAMP DEFAULT NOW()
    - last_login: TIMESTAMP
    - active: BOOLEAN DEFAULT TRUE
    """
    
    def __init__(self):
        """Initialize Supabase authentication manager"""
        self._init_supabase()
        self._load_settings()
    
    def _load_settings(self):
        """Load authentication settings from app_config.py"""
        self.allow_signup = ALLOW_SIGNUP
    
    def _init_supabase(self):
        """Initialize Supabase client with custom auth table"""
        # Get credentials from environment or secrets
        try:
            supabase_url = st.secrets.get("SUPABASE_URL")
            supabase_key = st.secrets.get("SUPABASE_KEY")
            supabase_schema = st.secrets.get("SUPABASE_SCHEMA", "public")
            auth_table = st.secrets.get("AUTH_TABLE", "auth")
        except:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            supabase_schema = os.getenv("SUPABASE_SCHEMA", "public")
            auth_table = os.getenv("AUTH_TABLE", "auth")
        
        # Validate credentials
        if not supabase_url or not supabase_key:
            st.error("❌ Supabase credentials not configured")
            st.error("Please set SUPABASE_URL and SUPABASE_KEY in .env file")
            st.info("Run: python src/setup_auth.py to create the auth table")
            st.stop()
        
        if supabase_url == "https://your-project.supabase.co":
            st.error("❌ Please update SUPABASE_URL in .env with your actual Supabase project URL")
            st.stop()
        
        if "your-anon-key" in supabase_key or "your-key" in supabase_key:
            st.error("❌ Please update SUPABASE_KEY in .env with your actual Supabase anon key")
            st.stop()
        
        # Create Supabase client
        try:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            self.supabase_schema = supabase_schema
            self.auth_table = auth_table
            # Connection successful (silent)
        except Exception as e:
            st.error(f"❌ Failed to connect to Supabase: {str(e)}")
            st.error("Check your SUPABASE_URL and SUPABASE_KEY in .env")
            st.stop()
    
    def _hash_password_bcrypt(self, password: str) -> str:
        """Hash password using bcrypt (industry standard)"""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password_bcrypt(self, password: str, hashed: str) -> bool:
        """Verify password against bcrypt hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    def login(self, username: str, password: str) -> bool:
        """
        Authenticate user with Supabase auth table.
        
        Args:
            username: Username
            password: Password (will be verified against bcrypt hash)
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Query user from auth table
            table = self.supabase.schema(self.supabase_schema).table(self.auth_table)
            response = table.select("*")\
                .eq("username", username)\
                .eq("active", True)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                return False
            
            user_data = response.data[0]
            password_hash = user_data.get('password_hash')
            
            # Verify password with bcrypt
            if not password_hash or not self._verify_password_bcrypt(password, password_hash):
                return False
            
            # Login successful - create session
            st.session_state['authenticated'] = True
            st.session_state['user'] = {
                'id': user_data.get('id'),
                'username': user_data.get('username'),
                'name': user_data.get('name'),
                'role': user_data.get('role'),
                'email': f"{username}@planner.local"
            }
            
            # Update last_login timestamp
            try:
                from datetime import datetime
                table.update({'last_login': datetime.utcnow().isoformat()})\
                    .eq('username', username)\
                    .execute()
            except Exception as e:
                print(f"Warning: Could not update last_login: {e}")
            
            return True
            
        except Exception as e:
            print(f"Login error: {e}")
            return False
    
    def signup(self, username: str, name: str, password: str) -> bool:
        """
        Register new user in Supabase auth table.
        
        Args:
            username: Username (must be unique)
            name: User's full name
            password: Password (will be hashed with bcrypt)
            
        Returns:
            True if signup successful, False otherwise
        """
        try:
            # Hash the password with bcrypt
            password_hash = self._hash_password_bcrypt(password)
            
            # Get table reference
            table = self.supabase.schema(self.supabase_schema).table(self.auth_table)
            
            # Check if username already exists
            existing = table.select("username").eq("username", username).execute()
            
            if existing.data and len(existing.data) > 0:
                st.error("Username already taken. Please choose another.")
                return False
            
            # Insert new user
            response = table.insert({
                "username": username,
                "name": name,
                "password_hash": password_hash,
                "role": "user",
                "active": True
            }).execute()
            
            if response.data:
                return True
            else:
                st.error("Failed to create account. Please try again.")
                return False
                
        except Exception as e:
            error_msg = str(e).lower()
            if "duplicate" in error_msg or "unique" in error_msg:
                st.error("Username already exists. Please choose another.")
            else:
                st.error("Signup failed. Please try again.")
            return False
    
    def logout(self):
        """Logout current user"""
        st.session_state['authenticated'] = False
        st.session_state['user'] = None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('authenticated', False)
    
    def get_user(self) -> Optional[Dict]:
        """Get current user info"""
        return st.session_state.get('user')
    
    def require_auth(self):
        """
        Require authentication to access page.
        Shows login page if not authenticated.
        """
        if not self.is_authenticated():
            self.show_login_page()
            st.stop()
    
    def show_login_page(self):
        """Display beautiful login page - matching loading screen style"""
        
        # CRITICAL: Hide everything immediately to prevent flash
        st.markdown("""
        <style>
        /* ================================================================
           IMMEDIATE HIDE - Prevent any flash of sidebar or default UI
           ================================================================ */
        
        /* Hide sidebar completely - ALL possible selectors */
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"],
        [data-testid="stSidebarNav"],
        [data-testid="stSidebarNavItems"],
        [data-testid="stSidebarUserContent"],
        [data-testid="stSidebarCollapsedControl"],
        section[data-testid="stSidebar"],
        aside[data-testid="stSidebar"],
        div[data-testid="stSidebarCollapsedControl"],
        button[kind="header"],
        #MainMenu, footer, header,
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        .css-1dp5vir,
        .css-dvg0e9,
        .css-1d391kg,
        .st-emotion-cache-1cypcdb,
        .css-1544g2n,
        .st-emotion-cache-vk3wp9,
        .st-emotion-cache-1gwvy71,
        .st-emotion-cache-eczf16,
        .st-emotion-cache-h4xjwg,
        div[class*="stSidebar"],
        section[class*="stSidebar"],
        aside[class*="sidebar"],
        div[class*="sidebar"] {
            display: none !important;
            visibility: hidden !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
            height: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
            overflow: hidden !important;
            position: absolute !important;
            left: -9999px !important;
            top: -9999px !important;
            opacity: 0 !important;
            pointer-events: none !important;
            z-index: -9999 !important;
            transform: translateX(-100vw) !important;
        }
        
        /* Clean white background - like loading page */
        .stApp, body, html, .main {
            background: white !important;
        }
        
        /* Perfect centering - everything fits on screen - NO SCROLL */
        .main .block-container {
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            min-height: calc(100vh - 2rem) !important;
            padding: 1rem !important;
            padding-top: 0 !important;
            max-width: 100% !important;
            overflow: hidden !important;
        }
        
        /* Remove header space */
        header[data-testid="stHeader"] {
            height: 0 !important;
            min-height: 0 !important;
            padding: 0 !important;
        }
        
        /* Smooth animation - like loading page */
        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Auth content - NO BOX, just clean floating content like loading page */
        .auth-content-wrapper {
            text-align: center;
            animation: slideUp 0.6s ease-out;
            max-width: 420px;
            width: 100%;
            margin: 0 auto;
        }
        
        /* Branding - exact same as loading page */
        .auth-icon {
            width: 56px;
            height: 56px;
            margin-bottom: 0.5rem;
            display: block;
            margin-left: auto;
            margin-right: auto;
        }
        
        .auth-title {
            color: #6495ED;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
            letter-spacing: 0.05em;
        }
        
        .auth-subtitle {
            color: #6b7280;
            font-size: 1.2rem;
            font-weight: 400;
            margin-bottom: 1.5rem;
            line-height: 1.4;
        }
        
        /* Divider - exact same as loading page */
        .auth-divider {
            width: 60px;
            height: 3px;
            background: linear-gradient(90deg, #6495ED 0%, #ff7f0e 100%);
            margin: 0.75rem auto 1.5rem auto;
            border-radius: 2px;
        }
        
        /* Clean tabs inside box - COMPACT */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            justify-content: center;
            background: transparent;
            border-bottom: 2px solid #f0f0f0;
            padding: 0 0 0.4rem 0;
            margin-bottom: 1rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent !important;
            border: none;
            border-bottom: 3px solid transparent;
            padding: 0.5rem 1.25rem !important;
            font-weight: 600;
            font-size: 0.9rem !important;
            color: #9ca3af;
            transition: all 0.2s ease;
            margin-bottom: -2px;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            color: #6495ED;
        }
        
        .stTabs [aria-selected="true"] {
            color: #6495ED !important;
            border-bottom-color: #6495ED !important;
        }
        
        .stTabs [data-baseweb="tab-panel"] {
            padding: 0;
        }
        
        /* Clean input fields with proper spacing - COMPACT */
        .stTextInput > div > div > input {
            border-radius: 8px;
            border: 1px solid #e5e7eb !important;
            padding: 10px 12px !important;
            font-size: 0.9rem !important;
            transition: all 0.2s ease;
            background: #fafafa !important;
            height: 38px !important;
            color: #111827 !important;
            box-shadow: none !important;
            width: 100% !important;
        }
        
        /* Fix autocomplete yellow background */
        .stTextInput > div > div > input:-webkit-autofill,
        .stTextInput > div > div > input:-webkit-autofill:hover,
        .stTextInput > div > div > input:-webkit-autofill:focus,
        .stTextInput > div > div > input:-webkit-autofill:active {
            -webkit-box-shadow: 0 0 0 30px #fafafa inset !important;
            -webkit-text-fill-color: #111827 !important;
        }
        
        .stTextInput > div > div > input:hover {
            background: #f5f5f5 !important;
            border-color: #d1d5db !important;
        }
        
        .stTextInput > div > div > input:focus {
            background: white !important;
            border-color: #6495ED !important;
            box-shadow: 0 0 0 3px rgba(100, 149, 237, 0.08) !important;
            outline: none !important;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: #9ca3af !important;
        }
        
        .stTextInput > label {
            display: none !important;
        }
        
        /* Clean button with proper spacing - COMPACT */
        .stButton > button {
            width: 100%;
            background: linear-gradient(135deg, #6495ED 0%, #5585E8 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px;
            padding: 10px 20px !important;
            font-size: 0.95rem !important;
            font-weight: 600;
            transition: all 0.25s ease;
            margin-top: 0.5rem;
            height: 40px !important;
            box-shadow: 0 3px 12px rgba(100, 149, 237, 0.25) !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 20px rgba(100, 149, 237, 0.35) !important;
        }
        
        .stButton > button:active {
            transform: translateY(0) !important;
        }
        
        /* Compact alerts inside form */
        div[data-baseweb="notification"] {
            border-radius: 6px;
            border: none;
            font-size: 0.825rem !important;
            padding: 0.5rem 0.75rem !important;
            margin: 0.4rem 0 !important;
            box-shadow: none;
        }
        
        div[data-baseweb="notification"][kind="error"] {
            background: #fef2f2 !important;
            color: #991b1b !important;
            border-left: 3px solid #ef4444;
        }
        
        div[data-baseweb="notification"][kind="success"] {
            background: #ecfdf5 !important;
            color: #065f46 !important;
            border-left: 3px solid #10b981;
        }
        
        /* Form with visible borders and padding - COMPACT */
        .stForm {
            padding: 1.25rem 1.75rem 1rem 1.75rem !important;
            background: white !important;
            max-width: 400px !important;
            margin: 0 auto !important;
            border: 2px solid #e5e7eb !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06) !important;
        }
        
        .element-container {
            margin-bottom: 0.5rem !important;
        }
        
        /* Ensure no overflow or cramping */
        .stTextInput, .stButton {
            margin-left: 0 !important;
            margin-right: 0 !important;
        }
        
        /* Tabs container with visible border - COMPACT */
        .stTabs {
            margin: 0 auto 0 auto;
            max-width: 400px;
            padding: 1rem 1.75rem 0 1.75rem;
            background: white;
            border: 2px solid #e5e7eb;
            border-radius: 12px 12px 0 0;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
        }
        
        /* Make sure form connects to tabs */
        .stTabs + div .stForm {
            border-radius: 0 0 12px 12px !important;
            border-top: none !important;
            margin-top: 0 !important;
        }
        
        /* Status footer - very compact */
        .auth-status {
            margin-top: 0.75rem;
            padding-top: 0.75rem;
            border-top: 1px solid #f0f0f0;
            max-width: 400px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .status-item {
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            color: #9ca3af;
            font-size: 0.75rem;
            margin: 0 0.5rem;
        }
        
        .status-icon {
            color: #10b981;
            font-weight: bold;
            font-size: 0.8rem;
        }
        
        /* Smooth spinner */
        .stSpinner > div {
            border-color: #6495ED transparent transparent transparent !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Branding - compact, no subtitle to save space
        logo_html = get_logo_html(width="72px", height="auto", margin_bottom="0.5rem")
        st.markdown(f"""
        <div style="text-align: center; margin: 0 auto 1rem auto; width: 100%;">
            {logo_html}
            <h1 style="color: #6495ED; font-size: 2rem; font-weight: 700; margin-bottom: 0; letter-spacing: 0.05em;">Anticipa</h1>
            <div style="width: 60px; height: 3px; background: linear-gradient(90deg, #6495ED 0%, #ff7f0e 100%); margin: 0.75rem auto; border-radius: 2px;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Clean tabs for login/signup
        if self.allow_signup:
            tab1, tab2 = st.tabs(["Login", "Sign Up"])
            
            with tab1:
                self._show_login_form()
            
            with tab2:
                self._show_signup_form()
        else:
            # Single login form without tabs
            self._show_login_form()
        
        # Status footer - like loading page
        st.markdown("""
        <div class="auth-status" style="text-align: center;">
            <div>
                <span class="status-item">
                    <span class="status-icon">✓</span>
                    <span>Secure Authentication</span>
                </span>
                <span class="status-item">
                    <span class="status-icon">✓</span>
                    <span>Encrypted Connection</span>
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _show_login_form(self):
        """Clean, minimal login form"""
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "Username",
                placeholder="Username",
                autocomplete="username",
                key="login_username",
                label_visibility="collapsed"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Password",
                autocomplete="current-password",
                key="login_password",
                label_visibility="collapsed"
            )
            
            submit = st.form_submit_button("Sign In", width='stretch')
            
            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    if self.login(username, password):
                        # Show white overlay immediately to prevent flash
                        st.markdown("""
                        <style>
                            .stApp > * { opacity: 0 !important; }
                            .stApp::before {
                                content: '';
                                position: fixed;
                                top: 0;
                                left: 0;
                                width: 100vw;
                                height: 100vh;
                                background: white;
                                z-index: 99999;
                            }
                        </style>
                        """, unsafe_allow_html=True)
                        st.session_state.show_loading_screen = True
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
    
    def _show_signup_form(self):
        """Clean, minimal signup form"""
        with st.form("signup_form", clear_on_submit=True):
            name = st.text_input(
                "Full Name",
                placeholder="Full Name",
                key="signup_name",
                label_visibility="collapsed"
            )
            
            username = st.text_input(
                "Username",
                placeholder="Username",
                autocomplete="username",
                key="signup_username",
                label_visibility="collapsed"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Password (min 6 characters)",
                autocomplete="new-password",
                key="signup_password",
                label_visibility="collapsed"
            )
            
            password_confirm = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Confirm Password",
                autocomplete="new-password",
                key="signup_password_confirm",
                label_visibility="collapsed"
            )
            
            submit = st.form_submit_button("Create Account", width='stretch')
            
            if submit:
                # Validation
                if not name or not username or not password or not password_confirm:
                    st.error("Please fill in all fields")
                    return
                
                if len(username) < 3:
                    st.error("Username must be at least 3 characters")
                    return
                
                if ' ' in username:
                    st.error("Username cannot contain spaces")
                    return
                
                if len(password) < 6:
                    st.error("Password must be at least 6 characters")
                    return
                
                if password != password_confirm:
                    st.error("Passwords do not match")
                    return
                
                # Attempt signup
                with st.spinner("Creating your account..."):
                    if self.signup(username, name, password):
                        st.success("Account created successfully! Switch to Login tab")
                        st.balloons()


def show_user_menu(auth_manager: AuthManager):
    """
    Display user menu in sidebar.
    
    Args:
        auth_manager: AuthManager instance
    """
    user = auth_manager.get_user()
    
    if user:
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"👤 **{user.get('name', user.get('username', 'User'))}**")
            st.caption(f"@{user.get('username')} • {user.get('role', 'user')}")
            
            if st.button("🚪 Logout", width='stretch'):
                auth_manager.logout()
                st.rerun()
