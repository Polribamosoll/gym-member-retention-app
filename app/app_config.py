"""
Application Configuration
Centralized settings for the Member Retention app
"""

# =============================================================================
# AUTHENTICATION SETTINGS
# =============================================================================

# Allow new user registration
# Set to False in production to prevent unauthorized signups
ALLOW_SIGNUP = False

# Default login credentials for demo mode (if Supabase not configured)
DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo123"

# =============================================================================
# APPLICATION SETTINGS
# =============================================================================

# App title
APP_TITLE = "Gym Member Retention App"
APP_SUBTITLE = "Supply Chain Optimization Platform"

# Default origin for routing (Barcelona postal code)
DEFAULT_ORIGIN = "08020"

# =============================================================================
# DEPLOYMENT SETTINGS
# =============================================================================

# Set this to True in production to enforce stricter validation
PRODUCTION_MODE = False

# Session timeout (in seconds)
SESSION_TIMEOUT = 3600  # 1 hour

# Maximum file upload size (MB)
MAX_UPLOAD_SIZE_MB = 50

# =============================================================================
# FEATURE FLAGS
# =============================================================================

# Enable/disable specific features
ENABLE_DATA_UPLOAD = True
ENABLE_DEMO_DATA_GENERATION = True
ENABLE_CSV_DOWNLOAD = True
ENABLE_DATA_VALIDATION = True

# =============================================================================
# NOTES
# =============================================================================
# This file contains application-level configuration that doesn't contain
# secrets. For sensitive data (API keys, database credentials), use:
# - Local development: .env file
# - Production: Environment variables in Render/Streamlit Cloud
