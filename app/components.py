"""
Shared UI components for Member Retention dashboard
"""
import streamlit as st
from theme import PRIMARY_COLOR, ACCENT_COLOR, TEXT_LIGHT, TEXT_DARK, BORDER_COLOR


def page_header(icon, title, description):
    """Display modern, clean page header"""
    st.markdown(f"""
    <div style='margin-bottom: 2.5rem;'>
        <div style='display: flex; align-items: center; gap: 1.25rem; margin-bottom: 0.75rem;'>
            <span style='font-size: 2.75rem;'>{icon}</span>
            <h1 style='margin: 0; font-size: 2.25rem; font-weight: 700; color: #1f2937; letter-spacing: -0.01em;'>{title}</h1>
        </div>
        <p style='font-size: 1.05rem; color: #6b7280; margin: 0; padding-left: 4rem; line-height: 1.6;'>{description}</p>
    </div>
    <hr style='border: none; border-top: 2px solid #e5e7eb; margin: 0 0 2rem 0;'>
    """, unsafe_allow_html=True)


def info_card(title, value, icon="📊", color=None):
    """Display modern info card with cornflower blue"""
    if color is None:
        color = PRIMARY_COLOR
    st.markdown(f"""
    <div style='background: white; 
                border: 2px solid #e5e7eb;
                border-left: 4px solid {color}; 
                border-radius: 12px; 
                padding: 1.5rem; 
                margin: 1rem 0;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
                transition: all 0.3s ease;'>
        <div style='display: flex; align-items: center; gap: 1.25rem;'>
            <span style='font-size: 2.25rem;'>{icon}</span>
            <div>
                <div style='font-size: 0.875rem; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em;'>{title}</div>
                <div style='font-size: 1.75rem; font-weight: 700; color: {color}; margin-top: 0.35rem;'>{value}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def section_divider(text=""):
    """Display a section divider with optional text"""
    if text:
        st.markdown(f"""
        <div style='display: flex; align-items: center; margin: 2rem 0 1.5rem;'>
            <div style='flex: 1; height: 2px; background: linear-gradient(to right, #e2e8f0, transparent);'></div>
            <span style='padding: 0 1.5rem; font-size: 0.9rem; font-weight: 600; color: #718096; text-transform: uppercase; letter-spacing: 0.1em;'>{text}</span>
            <div style='flex: 1; height: 2px; background: linear-gradient(to left, #e2e8f0, transparent);'></div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='height: 2px; background: linear-gradient(to right, #e2e8f0, transparent, #e2e8f0); margin: 2rem 0;'></div>
        """, unsafe_allow_html=True)


def action_button_row(buttons):
    """Display a row of action buttons with consistent spacing"""
    cols = st.columns(len(buttons))
    for idx, (label, key, callback) in enumerate(buttons):
        with cols[idx]:
            if st.button(label, key=key, width="stretch", type="primary"):
                callback()


def metric_card(label, value, delta=None, icon="📊"):
    """Modern metric card with cornflower blue"""
    delta_html = ""
    if delta:
        delta_color = "#10b981" if delta > 0 else "#ef4444"
        delta_symbol = "▲" if delta > 0 else "▼"
        delta_html = f"<div style='font-size: 0.95rem; color: {delta_color}; font-weight: 600; margin-top: 0.5rem;'>{delta_symbol} {abs(delta):.1f}%</div>"
    
    st.markdown(f"""
    <div style='background: white; 
                border: 2px solid #e5e7eb; 
                border-radius: 12px; 
                padding: 1.75rem; 
                text-align: center;
                transition: all 0.3s ease;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);'>
        <div style='font-size: 2.25rem; margin-bottom: 1rem;'>{icon}</div>
        <div style='font-size: 0.875rem; font-weight: 600; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.75rem;'>{label}</div>
        <div style='font-size: 2.25rem; font-weight: 700; color: {PRIMARY_COLOR};'>{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def status_badge(text, status="info"):
    """Display modern status badge"""
    colors = {
        "success": (ACCENT_COLOR, "#ecfdf5"),
        "warning": ("#f59e0b", "#fffbeb"),
        "error": ("#ef4444", "#fef2f2"),
        "info": (PRIMARY_COLOR, "#eff6ff")
    }
    color, bg = colors.get(status, colors["info"])
    
    st.markdown(f"""
    <span style='display: inline-block; 
                 background: {bg}; 
                 color: {color}; 
                 padding: 0.4rem 1rem; 
                 border-radius: 24px; 
                 font-size: 0.875rem; 
                 font-weight: 600;
                 border: 2px solid {color};'>{text}</span>
    """, unsafe_allow_html=True)


def progress_steps(steps, current_step):
    """Display modern progress steps with cornflower blue"""
    steps_html = []
    
    for idx, step in enumerate(steps):
        is_current = idx == current_step
        is_completed = idx < current_step
        
        if is_completed:
            color = ACCENT_COLOR
            icon = "✓"
        elif is_current:
            color = PRIMARY_COLOR
            icon = str(idx + 1)
        else:
            color = BORDER_COLOR
            icon = str(idx + 1)
        
        # Build step HTML
        step_html = f"<div style='display: flex; flex-direction: column; align-items: center;'><div style='width: 48px; height: 48px; border-radius: 50%; background: {color}; color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.15rem; box-shadow: 0 4px 12px {color}50;'>{icon}</div><div style='font-size: 0.8rem; font-weight: 600; color: {color}; margin-top: 0.75rem; text-align: center;'>{step}</div></div>"
        steps_html.append(step_html)
        
        # Add connector
        if idx < len(steps) - 1:
            connector_color = ACCENT_COLOR if is_completed else BORDER_COLOR
            connector_html = f"<div style='flex: 1; height: 3px; background: {connector_color}; margin: 0 1rem;'></div>"
            steps_html.append(connector_html)
    
    full_html = f"<div style='display: flex; align-items: center; margin: 2.5rem 0; padding: 2rem; background: white; border-radius: 16px; border: 2px solid #e5e7eb; box-shadow: 0 2px 12px rgba(0,0,0,0.06);'>{''.join(steps_html)}</div>"
    
    st.markdown(full_html, unsafe_allow_html=True)
