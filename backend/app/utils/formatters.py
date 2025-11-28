"""
VALORA Utility Functions - Formatters
"""

from typing import Union
from decimal import Decimal


def format_currency(value: Union[int, float, Decimal], currency: str = "USD") -> str:
    """
    Format a number as currency with appropriate suffix.
    
    Args:
        value: The numeric value to format
        currency: Currency code (default: USD)
    
    Returns:
        Formatted currency string (e.g., "$1.23T", "$456.78B")
    """
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "INR": "₹",
        "JPY": "¥",
        "CNY": "¥",
    }
    
    symbol = symbols.get(currency, "$")
    abs_value = abs(float(value))
    sign = "-" if value < 0 else ""
    
    if abs_value >= 1e12:
        return f"{sign}{symbol}{abs_value / 1e12:.2f}T"
    elif abs_value >= 1e9:
        return f"{sign}{symbol}{abs_value / 1e9:.2f}B"
    elif abs_value >= 1e6:
        return f"{sign}{symbol}{abs_value / 1e6:.2f}M"
    elif abs_value >= 1e3:
        return f"{sign}{symbol}{abs_value / 1e3:.2f}K"
    else:
        return f"{sign}{symbol}{abs_value:.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format a decimal as percentage.
    
    Args:
        value: Decimal value (e.g., 0.05 for 5%)
        decimals: Number of decimal places
    
    Returns:
        Formatted percentage string (e.g., "5.00%")
    """
    return f"{value * 100:.{decimals}f}%"


def format_change(value: float, decimals: int = 2) -> str:
    """
    Format a change value with + or - prefix.
    
    Args:
        value: The change value
        decimals: Number of decimal places
    
    Returns:
        Formatted change string (e.g., "+2.34%", "-1.56%")
    """
    prefix = "+" if value >= 0 else ""
    return f"{prefix}{value:.{decimals}f}%"


def format_large_number(value: Union[int, float]) -> str:
    """
    Format a large number with appropriate suffix.
    
    Args:
        value: The numeric value
    
    Returns:
        Formatted string (e.g., "1.5M", "2.3B")
    """
    abs_value = abs(float(value))
    sign = "-" if value < 0 else ""
    
    if abs_value >= 1e12:
        return f"{sign}{abs_value / 1e12:.1f}T"
    elif abs_value >= 1e9:
        return f"{sign}{abs_value / 1e9:.1f}B"
    elif abs_value >= 1e6:
        return f"{sign}{abs_value / 1e6:.1f}M"
    elif abs_value >= 1e3:
        return f"{sign}{abs_value / 1e3:.1f}K"
    else:
        return f"{sign}{abs_value:.0f}"


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human readable string.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted duration (e.g., "2h 30m 45s")
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{int(hours)}h")
    if minutes > 0:
        parts.append(f"{int(minutes)}m")
    if secs > 0 or not parts:
        parts.append(f"{int(secs)}s")
    
    return " ".join(parts)


def format_relative_time(timestamp: str) -> str:
    """
    Format timestamp as relative time.
    
    Args:
        timestamp: ISO format timestamp
    
    Returns:
        Relative time string (e.g., "5 minutes ago", "2 hours ago")
    """
    from datetime import datetime
    
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = now - dt
    
    seconds = int(diff.total_seconds())
    
    if seconds < 60:
        return f"{seconds}s ago"
    elif seconds < 3600:
        return f"{seconds // 60}m ago"
    elif seconds < 86400:
        return f"{seconds // 3600}h ago"
    elif seconds < 604800:
        return f"{seconds // 86400}d ago"
    else:
        return dt.strftime("%Y-%m-%d")
