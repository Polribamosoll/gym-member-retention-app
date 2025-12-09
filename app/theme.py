"""
Member Retention - Design System Theme Constants
Centralized color palette and design tokens for consistent theming
"""

# Primary Colors
PRIMARY_COLOR = "#6495ED"  # Cornflower Blue
PRIMARY_DARK = "#5585E8"
PRIMARY_LIGHT = "#84B0F5"

# Secondary Colors
SECONDARY_COLOR = "#7BA3F0"
ACCENT_COLOR = "#10b981"  # Green (success)
WARNING_COLOR = "#f59e0b"  # Orange
ERROR_COLOR = "#ef4444"  # Red

# Text Colors
TEXT_DARK = "#1f2937"
TEXT_MEDIUM = "#4b5563"
TEXT_LIGHT = "#6b7280"
TEXT_LIGHTER = "#9ca3af"

# Background Colors
BG_WHITE = "#ffffff"
BG_LIGHT = "#f9fafb"
BG_LIGHTER = "#f3f4f6"
BORDER_COLOR = "#e5e7eb"

# Gradients
PRIMARY_GRADIENT = f"linear-gradient(135deg, {PRIMARY_COLOR} 0%, {PRIMARY_DARK} 100%)"

# Chart Colors (matching brand palette)
CHART_COLORS = {
    'primary': PRIMARY_COLOR,
    'secondary': SECONDARY_COLOR,
    'success': ACCENT_COLOR,
    'warning': WARNING_COLOR,
    'danger': ERROR_COLOR,
    'blue': PRIMARY_COLOR,
    'green': ACCENT_COLOR,
    'orange': WARNING_COLOR,
    'red': ERROR_COLOR,
    'lightblue': "#B3D4FF",
    'lightgreen': "#A7F3D0",
}

# Chart Color Sequences
CHART_SEQUENCE = [PRIMARY_COLOR, SECONDARY_COLOR, ACCENT_COLOR, WARNING_COLOR, "#9333ea"]




