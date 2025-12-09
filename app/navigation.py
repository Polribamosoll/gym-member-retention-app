"""
Navigation components for Member Retention dashboard
"""
import streamlit as st


def navigate_to(page):
    """Navigate to a specific page"""
    st.session_state.current_page = page
    st.rerun()


def show_navigation_bar(current_module=None, auth_manager=None):
    """Display professional navigation bar"""
    # Minimal navigation styling (sidebar hiding now in styles.css)
    st.markdown("""
    <style>
        /* Navigation specific styles */
        .main .block-container {
            padding-top: 1rem !important;
        }
        
        /* Clean background */
        .stApp, .main, [data-testid="stAppViewContainer"] {
            background: white !important;
        }
        
        /* App title */
        .app-title {
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Arial', sans-serif;
            font-size: 1.5rem;
            font-weight: 600;
            color: #212529;
            letter-spacing: -0.01em;
            line-height: 1.2;
            display: flex;
            align-items: center;
        }
        
        /* User info */
        .user-info {
            text-align: right;
            font-size: 1rem;
            color: #495057;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 0.5rem;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Arial', sans-serif;
            padding-top: 0.25rem;
        }
        
        .user-info strong {
            color: #212529;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Top row: App logo & name on left, username on right
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown('<div class="app-title">Anticipa</div>', unsafe_allow_html=True)
    
    with col_right:
        if auth_manager:
            user = auth_manager.get_user()
            if user:
                st.markdown(f"""
                <div class='user-info'>
                    <span>👤 <strong>{user.get('name', user.get('username', 'User'))}</strong></span>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    # Bottom row: Navigation buttons + logout
    col1, col2, col3, col4, col5, col6 = st.columns([1.5, 1.2, 0.9, 0.9, 0.9, 1])
    
    with col1:
        if st.button("🏠 Home", key="nav_home", width='stretch'):
            navigate_to('landing')
    
    with col2:
        if st.button("⚙️ Data & Settings", key="nav_data", width='stretch', disabled=(current_module == 'data')):
            navigate_to('data')
    
    with col3:
        if st.button("📈 Forecast", key="nav_forecast", width='stretch', disabled=(current_module == 'forecast')):
            navigate_to('forecast')
    
    with col4:
        if st.button("📦 Inventory", key="nav_inventory", width='stretch', disabled=(current_module == 'inventory')):
            navigate_to('inventory')
    
    with col5:
        if st.button("🚚 Routing", key="nav_routing", width='stretch', disabled=(current_module == 'routing')):
            navigate_to('routing')
    
    with col6:
        if auth_manager:
            if st.button("🚪 Logout", key="logout_btn", width='stretch'):
                auth_manager.logout()
                st.rerun()
    
    st.markdown('<hr style="border: none; border-top: 2px solid #e5e7eb; margin: 1rem 0 0 0;">', unsafe_allow_html=True)
