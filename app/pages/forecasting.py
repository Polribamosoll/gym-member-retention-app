"""
Forecasting page module
"""
import streamlit as st
import pandas as pd
from pathlib import Path

from forecaster.forecaster import Forecaster
from utils.output_manager import OutputManager
from app_utils import create_forecast_chart
from components import page_header, section_divider, progress_steps
from pages.landing import show_footer

# Path to pre-trained demo model
DEMO_MODEL_PATH = Path(__file__).parent.parent.parent / "models" / "demo_forecaster.pkl"


def show_forecast_page(show_navigation_bar, navigate_to):
    """Display forecasting page"""
    show_navigation_bar('forecast')
    page_header("📈", "Demand Forecasting", "Predict future demand using LightGBM with automated feature engineering")
    
    # Show progress
    progress_steps(["Data", "Forecast", "Inventory", "Routing"], 1)
    
    if not st.session_state.data_generated:
        st.warning("⚠️ Please generate or upload data first")
        if st.button("← Go to Data & Settings", width='stretch'):
            navigate_to('data')
        return
    
    section_divider("Configuration")
    
    # Demo mode toggle - only show if pre-trained model exists AND using demo data
    demo_model_available = DEMO_MODEL_PATH.exists()
    is_demo_data = st.session_state.get('is_demo_data', False)
    
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.metric("Forecast Horizon", f"{st.session_state.forecast_horizon} weeks")
    with col_info2:
        st.metric("Model", "LightGBM")
    with col_info3:
        st.metric("Time Series", st.session_state.n_stores * st.session_state.n_products)
    
    # Demo mode option - only available with demo data
    if demo_model_available and is_demo_data:
        st.markdown("<br>", unsafe_allow_html=True)
        use_demo_model = st.checkbox(
            "⚡ Use pre-trained model (instant forecasting for demos)",
            value=True,
            help="Skip model training by using a pre-trained model. Much faster for demonstrations."
        )
    else:
        use_demo_model = False
        if not is_demo_data and st.session_state.data_generated:
            st.info("💡 Using uploaded data - model will be trained from scratch for best accuracy.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    button_label = "⚡ Generate Forecasts" if use_demo_model else "🤖 Train & Forecast"
    
    if st.button(button_label, key="forecast", width='stretch', type="primary"):
        data = st.session_state.data
        
        if use_demo_model and demo_model_available:
            # Fast path: use pre-trained model
            with st.spinner("Loading pre-trained model and generating forecasts..."):
                try:
                    forecaster = Forecaster.from_pretrained(str(DEMO_MODEL_PATH))
                    # Override forecast horizon from session state
                    forecaster.forecast_horizon = st.session_state.forecast_horizon
                    forecasts = forecaster.predict(data)
                    
                    st.session_state.forecasts = forecasts
                    st.session_state.forecasts_generated = True
                    st.success("✅ Forecasts generated instantly using pre-trained model!")
                except Exception as e:
                    st.error(f"Failed to load pre-trained model: {e}")
                    st.info("Falling back to training a new model...")
                    _train_and_forecast(data)
        else:
            # Standard path: train model from scratch
            _train_and_forecast(data)
    
    # Show results if forecasts have been generated
    _show_forecast_results(navigate_to)
    
    # Footer
    show_footer()


def _train_and_forecast(data):
    """Train model from scratch and generate forecasts"""
    with st.spinner("Training forecasting model... This may take a few minutes..."):
        split_date = data['date'].max() - pd.Timedelta(weeks=st.session_state.forecast_horizon)
        train_data = data[data['date'] <= split_date]
        
        forecaster = Forecaster(
            primary_keys=['store', 'product'],
            date_col='date',
            target_col='sales',
            frequency='W',
            forecast_horizon=st.session_state.forecast_horizon
        )
        forecaster.fit(train_data)
        
        forecasts = forecaster.predict(data)
        
        st.session_state.forecasts = forecasts
        st.session_state.forecasts_generated = True
        st.success("✅ Forecasts generated successfully!")


def _show_forecast_results(navigate_to):
    """Display forecast results after generation"""
    if st.session_state.forecasts_generated:
        forecasts = st.session_state.forecasts
        
        section_divider("Results")
        st.markdown("#### Forecasts vs Actuals")
        
        stores = sorted(forecasts['store'].unique())
        products = sorted(forecasts['product'].unique())
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            selected_store = st.selectbox("Select Store", stores)
        with col_s2:
            selected_product = st.selectbox("Select Product", products)
        
        subset = forecasts[
            (forecasts['store'] == selected_store) & 
            (forecasts['product'] == selected_product)
        ]
        
        fig = create_forecast_chart(subset)
        fig.update_layout(title=f'Store {selected_store} - Product {selected_product}')
        st.plotly_chart(fig, width='stretch', key="forecast_chart")
        
        with st.expander("📋 View Forecast Data"):
            st.dataframe(subset, width='stretch')
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Save button
        col_save1, col_save2, col_save3 = st.columns([1, 1, 1])
        with col_save2:
            if st.button("💾 Save Forecasts to CSV", width='stretch'):
                output_mgr = OutputManager()
                filepath = output_mgr.save_forecasts(forecasts)
                st.success(f"✅ Forecasts saved to {filepath.name}")
        
        col_next1, col_next2, col_next3 = st.columns([1, 1, 1])
        with col_next2:
            if st.button("Next: Inventory Optimization →", width='stretch', type="primary"):
                navigate_to('inventory')
    else:
        st.info("👆 Click the button above to generate predictions")
