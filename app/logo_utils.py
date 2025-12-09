"""
Logo utility functions for Anticipa app
Handles logo encoding and display
"""

import base64
from pathlib import Path


def get_logo_base64():
    """
    Get the Anticipa logo as base64 encoded string
    Returns the data URI for use in HTML img src
    """
    logo_path = Path(__file__).parent.parent / "img" / "anticipa_logo_clean.png"
    
    if not logo_path.exists():
        # Fallback to truck emoji if logo not found
        return None
    
    try:
        with open(logo_path, "rb") as f:
            logo_bytes = f.read()
        logo_base64 = base64.b64encode(logo_bytes).decode()
        return f"data:image/png;base64,{logo_base64}"
    except Exception as e:
        print(f"Error loading logo: {e}")
        return None


def get_logo_html(width="80px", height="auto", margin_bottom="1rem", extra_style=""):
    """
    Get HTML for displaying the logo with perfect centering
    
    Args:
        width: CSS width value
        height: CSS height value (use 'auto' to maintain aspect ratio)
        margin_bottom: CSS margin-bottom value
        extra_style: Additional CSS styles
    
    Returns:
        HTML string with img tag wrapped in centered container
    """
    logo_data = get_logo_base64()
    
    if logo_data:
        return f'''<div style="display: flex; justify-content: center; align-items: center; width: 100%; margin-bottom: {margin_bottom}; padding-right: 8px;">
            <img src="{logo_data}" style="width: {width}; height: {height}; object-fit: contain; {extra_style}" />
        </div>'''
    else:
        # Fallback to truck emoji
        return f'<div style="font-size: {width}; margin-bottom: {margin_bottom}; display: flex; justify-content: center; align-items: center; width: 100%;">🚚</div>'


def get_favicon_base64():
    """
    Get the Anticipa logo as base64 for use as favicon
    Returns the base64 string without the data URI prefix
    """
    logo_path = Path(__file__).parent.parent / "img" / "anticipa_logo_clean.png"
    
    if not logo_path.exists():
        return None
    
    try:
        with open(logo_path, "rb") as f:
            logo_bytes = f.read()
        return base64.b64encode(logo_bytes).decode()
    except Exception as e:
        print(f"Error loading favicon: {e}")
        return None
