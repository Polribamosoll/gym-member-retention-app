"""
Loading Screen Component
Beautiful loading screen shown during data initialization.
"""

import streamlit as st
import time
from typing import Optional
from theme import PRIMARY_COLOR, WARNING_COLOR, ACCENT_COLOR, TEXT_LIGHT
from logo_utils import get_logo_html


def render_loading_screen(message: str = "Preparing your workspace...", 
                          submessage: Optional[str] = None):
    """
    Render a beautiful loading screen with animation
    
    Args:
        message: Main loading message
        submessage: Optional secondary message
    """
    BRAND_NAME = "Anticipa"
    PAGE_TITLE = "Supply Chain Optimization Platform"
    PAGE_ICON = "🚚"
    BRAND_COLOR = PRIMARY_COLOR
    ACCENT_COLOR = WARNING_COLOR
    
    # CRITICAL: Hide everything immediately to prevent flash
    st.markdown("""
    <style>
        /* ================================================================
           IMMEDIATE HIDE - Prevent any flash of sidebar or default UI
           ================================================================ */
        
        /* Hide Streamlit default elements */
        header {visibility: hidden !important;}
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        
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
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
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
        
        /* Clean white background */
        .stApp, body, html, .main {
            background: white !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Build submessage HTML if provided
    submessage_html = ""
    if submessage:
        submessage_html = f'<div style="color: {TEXT_LIGHT}; font-size: 1rem; margin-bottom: 2rem;">{submessage}</div>'
    
    # Get logo HTML - bigger and centered
    logo_html = get_logo_html(width="80px", height="auto", margin_bottom="1rem")
    
    # Create full-page loading overlay
    html_content = f"""
    <div class="loading-overlay">
        <div class="loading-content" style="text-align: center; padding: 2rem;">
            {logo_html}
            <h1 style="color: {BRAND_COLOR}; font-size: 2.5rem; font-weight: 700; margin-bottom: 0.5rem; letter-spacing: 0.05em;">{BRAND_NAME}</h1>
            <h2 style="color: {TEXT_LIGHT}; font-size: 1.5rem; font-weight: 400; margin-bottom: 3rem;">{PAGE_TITLE}</h2>
            <div class="loading-spinner"></div>
            <div style="color: #374151; font-size: 1.25rem; font-weight: 500; margin-bottom: 0.5rem;">{message}<span class="loading-dots">...</span></div>
            {submessage_html}
            <div style="max-width: 400px; width: 100%; margin: 0 auto;">
                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
            </div>
            <div style="margin-top: 3rem; color: {TEXT_LIGHT}; font-size: 0.9rem; max-width: 500px; margin-left: auto; margin-right: auto;">
                <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 1rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="color: {ACCENT_COLOR};">✓</span>
                        <span>Authentication</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="color: {PRIMARY_COLOR};">⟳</span>
                        <span>Loading Data</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="color: {TEXT_LIGHT};">○</span>
                        <span>Initializing</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    
    st.markdown(html_content, unsafe_allow_html=True)


def show_loading_screen_after_login():
    """
    Show loading screen for 2 seconds after successful login
    """
    if st.session_state.get('show_loading_screen', False):
        render_loading_screen(
            message="Loading your workspace",
            submessage="This will only take a moment"
        )
        
        # Wait 2 seconds (reduced from 5 for better UX)
        time.sleep(2)
        
        # Clear the loading screen flag
        st.session_state.show_loading_screen = False
        
        # Rerun to show the main app
        st.rerun()
        return True
    
    return False

