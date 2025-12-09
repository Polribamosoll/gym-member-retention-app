"""
Landing page module
"""
import streamlit as st
from logo_utils import get_logo_html


def show_footer():
    """Display footer on all pages"""
    st.markdown("""
    <div style='text-align: center; background: white; color: #718096; padding: 2rem; margin-top: 3rem; border-top: 1px solid #e2e8f0;'>
        <p style='font-size: 1.1rem; font-weight: 700; margin: 0; letter-spacing: 0.08em; color: #6495ED;'>ANTICIPA - 2025</p>
        <p style='font-size: 1rem; margin-top: 0.5rem; color: #6b7280;'>Supply Chain Optimization Platform</p>
    </div>
    """, unsafe_allow_html=True)


def show_landing_page(navigate_to):
    """Display clean landing page with cornflower blue theme"""
    # Get logo HTML - bigger and slightly left
    logo_html = get_logo_html(width="64px", height="auto", margin_bottom="0.5rem", extra_style="margin-right: 16px;")
    
    # Hero section with cornflower blue branding
    st.markdown(f"""
    <style>
        /* Landing page with cornflower blue theme */
        .stApp {{background: white !important;}}
        .main {{background: white !important;}}
        
        /* Hero - clean with visible border - SHORTER */
        .landing-hero {{
            text-align: center;
            padding: 1.5rem 1.5rem !important;
            margin-bottom: 2rem;
            background: white;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            border: 2px solid #6495ED;
        }}
        
        /* Module cards with visible borders - SHORTER */
        .module-card {{
            background: white !important;
            border-radius: 12px;
            padding: 1.4rem !important;
            margin: 0.75rem 0;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
            border: 2px solid #e5e7eb;
            transition: all 0.3s ease;
            height: 100%;
            min-height: auto !important;
        }}
        
        .module-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(100, 149, 237, 0.2);
            border-color: #6495ED;
        }}
        
        .module-icon {{
            font-size: 2.5rem;
            margin-bottom: 0.6rem;
            display: block;
        }}
        
        .module-title {{
            font-size: 1.3rem;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 0.5rem;
        }}
        
        .module-description {{
            font-size: 0.9rem;
            color: #6b7280;
            line-height: 1.5;
            margin-bottom: 0.7rem;
        }}
        
        .module-features {{
            list-style: none;
            padding: 0;
            margin: 0;
            font-size: 0.85rem;
            color: #9ca3af;
        }}
        
        .module-features li {{
            padding: 0.25rem 0;
        }}
        
        .module-features li:before {{
            content: '✓ ';
            color: #10b981;
            font-weight: bold;
        }}
    </style>
    
    <div class="landing-hero">
        {logo_html}
        <h1 style="color: #6495ED; font-size: 2.2rem; font-weight: 700; margin-bottom: 0.3rem; letter-spacing: 0.02em;">Anticipa</h1>
        <h2 style="color: #6b7280; font-size: 1.2rem; font-weight: 500; margin-bottom: 0.5rem;">Supply Chain Optimization Platform</h2>
        <p style="color: #9ca3af; font-size: 0.95rem; margin: 0;">Forecast demand • Optimize inventory • Route deliveries</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Responsive grid - 2 columns on desktop, 1 on mobile
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        st.markdown("""
        <div class="module-card">
            <span class="module-icon">⚙️</span>
            <div class="module-title">Data & Settings</div>
            <div class="module-description">
                Configure system parameters and load data for analysis
            </div>
            <ul class="module-features">
                <li>Upload your own data</li>
                <li>Generate synthetic demo data</li>
                <li>Configure all module settings</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Launch Module", key="btn_data", width='stretch', type="primary"):
            navigate_to('data')
    
    with col2:
        st.markdown("""
        <div class="module-card">
            <span class="module-icon">📈</span>
            <div class="module-title">Demand Forecasting</div>
            <div class="module-description">
                Predict future demand using LightGBM with automated feature engineering
            </div>
            <ul class="module-features">
                <li>Gradient boosting model</li>
                <li>Automated features</li>
                <li>No data leakage</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Launch Module", key="btn_forecast", width='stretch', type="primary"):
            navigate_to('forecast')
    
    col3, col4 = st.columns(2, gap="medium")
    
    with col3:
        st.markdown("""
        <div class="module-card">
            <span class="module-icon">📦</span>
            <div class="module-title">Inventory Optimization</div>
            <div class="module-description">
                Optimize stock levels using reorder point policies with safety stock
            </div>
            <ul class="module-features">
                <li>Reorder point calculation</li>
                <li>Safety stock optimization</li>
                <li>Stockout prevention</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Launch Module", key="btn_inventory", width='stretch', type="primary"):
            navigate_to('inventory')
    
    with col4:
        st.markdown("""
        <div class="module-card">
            <span class="module-icon">🚚</span>
            <div class="module-title">Delivery Routing</div>
            <div class="module-description">
                Optimize delivery routes with intelligent truck assignment
            </div>
            <ul class="module-features">
                <li>Smart truck assignment</li>
                <li>Route optimization</li>
                <li>Payload management</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Launch Module", key="btn_routing", width='stretch', type="primary"):
            navigate_to('routing')
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    show_footer()
