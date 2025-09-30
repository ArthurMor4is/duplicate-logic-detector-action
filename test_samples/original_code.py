#!/usr/bin/env python3
"""
Original code file with various functions that will be duplicated in other files.
This simulates an existing codebase with established functionality.
"""

import re
import json
from typing import List, Dict, Optional


def validate_email(email: str) -> bool:
    """
    Validate email address format using regex.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def calculate_discount(price: float, percentage: float) -> float:
    """
    Calculate discount amount based on price and percentage.
    
    Args:
        price: Original price
        percentage: Discount percentage (0-100)
        
    Returns:
        Discount amount
    """
    if percentage < 0 or percentage > 100:
        raise ValueError("Percentage must be between 0 and 100")
    
    return price * (percentage / 100)


def process_user_data(users: List[Dict]) -> List[Dict]:
    """
    Process and validate user data from a list.
    
    Args:
        users: List of user dictionaries
        
    Returns:
        List of processed user data
    """
    processed_users = []
    
    for user in users:
        if not user.get('email'):
            continue
            
        # Validate email
        if not validate_email(user['email']):
            continue
            
        # Add processed flag
        user['processed'] = True
        user['status'] = 'active'
        
        processed_users.append(user)
    
    return processed_users


def format_currency(amount: float, currency: str = 'USD') -> str:
    """
    Format amount as currency string.
    
    Args:
        amount: Monetary amount
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    if currency == 'USD':
        return f"${amount:.2f}"
    elif currency == 'EUR':
        return f"€{amount:.2f}"
    elif currency == 'GBP':
        return f"£{amount:.2f}"
    else:
        return f"{amount:.2f} {currency}"


def parse_json_config(config_path: str) -> Dict:
    """
    Parse JSON configuration file.
    
    Args:
        config_path: Path to JSON config file
        
    Returns:
        Parsed configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config: {e}")
        return {}


def calculate_tax(amount: float, tax_rate: float) -> float:
    """
    Calculate tax amount based on amount and tax rate.
    
    Args:
        amount: Base amount
        tax_rate: Tax rate as decimal (e.g., 0.08 for 8%)
        
    Returns:
        Tax amount
    """
    if tax_rate < 0:
        raise ValueError("Tax rate cannot be negative")
    
    return amount * tax_rate


def filter_active_items(items: List[Dict]) -> List[Dict]:
    """
    Filter list to only include active items.
    
    Args:
        items: List of item dictionaries
        
    Returns:
        List of active items only
    """
    active_items = []
    
    for item in items:
        if item.get('status') == 'active' or item.get('active', False):
            active_items.append(item)
    
    return active_items


def generate_user_report(users: List[Dict]) -> Dict:
    """
    Generate summary report for users.
    
    Args:
        users: List of user dictionaries
        
    Returns:
        Summary report dictionary
    """
    total_users = len(users)
    active_users = len([u for u in users if u.get('status') == 'active'])
    
    return {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': total_users - active_users,
        'activity_rate': active_users / total_users if total_users > 0 else 0
    }
