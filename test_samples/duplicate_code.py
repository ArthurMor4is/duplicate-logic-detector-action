#!/usr/bin/env python3
"""
Duplicate code file that recreates functionality from original_code.py
This simulates a scenario where developers have unknowingly duplicated existing logic.
"""

import re
import json
from typing import List, Dict, Optional


def check_email_format(email_address: str) -> bool:
    """
    Check if email address has valid format.
    
    Args:
        email_address: Email to check
        
    Returns:
        True if format is valid, False otherwise
    """
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email_address) is not None


def compute_discount_amount(original_price: float, discount_percent: float) -> float:
    """
    Compute the discount amount for a given price and percentage.
    
    Args:
        original_price: The original price
        discount_percent: Discount percentage (0-100)
        
    Returns:
        Amount of discount
    """
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount percentage must be between 0 and 100")
    
    return original_price * (discount_percent / 100)


def validate_and_process_users(user_list: List[Dict]) -> List[Dict]:
    """
    Validate and process a list of user data.
    
    Args:
        user_list: List of user dictionaries
        
    Returns:
        List of validated and processed users
    """
    valid_users = []
    
    for user_data in user_list:
        if not user_data.get('email'):
            continue
            
        # Check email format
        if not check_email_format(user_data['email']):
            continue
            
        # Mark as processed
        user_data['processed'] = True
        user_data['status'] = 'active'
        
        valid_users.append(user_data)
    
    return valid_users


def format_money(value: float, currency_code: str = 'USD') -> str:
    """
    Format monetary value as currency string.
    
    Args:
        value: Money amount
        currency_code: Currency code
        
    Returns:
        Formatted money string
    """
    if currency_code == 'USD':
        return f"${value:.2f}"
    elif currency_code == 'EUR':
        return f"€{value:.2f}"
    elif currency_code == 'GBP':
        return f"£{value:.2f}"
    else:
        return f"{value:.2f} {currency_code}"


def load_json_configuration(file_path: str) -> Dict:
    """
    Load JSON configuration from file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(file_path, 'r') as file:
            configuration = json.load(file)
        return configuration
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"Configuration loading error: {error}")
        return {}


def compute_tax_amount(base_amount: float, rate: float) -> float:
    """
    Compute tax amount for a base amount and tax rate.
    
    Args:
        base_amount: Base amount for tax calculation
        rate: Tax rate as decimal
        
    Returns:
        Calculated tax amount
    """
    if rate < 0:
        raise ValueError("Tax rate must not be negative")
    
    return base_amount * rate


def get_active_items_only(item_list: List[Dict]) -> List[Dict]:
    """
    Get only the active items from a list.
    
    Args:
        item_list: List of items
        
    Returns:
        Filtered list with active items only
    """
    result = []
    
    for item in item_list:
        if item.get('status') == 'active' or item.get('active', False):
            result.append(item)
    
    return result


def create_user_summary(user_data: List[Dict]) -> Dict:
    """
    Create a summary report for user data.
    
    Args:
        user_data: List of user dictionaries
        
    Returns:
        User summary report
    """
    user_count = len(user_data)
    active_count = len([user for user in user_data if user.get('status') == 'active'])
    
    return {
        'total_users': user_count,
        'active_users': active_count,
        'inactive_users': user_count - active_count,
        'activity_rate': active_count / user_count if user_count > 0 else 0
    }


# Additional function with high similarity but different implementation approach
def email_validator(email_str: str) -> bool:
    """
    Validate email address using different approach but same logic.
    
    Args:
        email_str: Email string to validate
        
    Returns:
        Validation result
    """
    # Same regex pattern but stored differently
    valid_email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    match_result = re.match(valid_email_pattern, email_str)
    return match_result is not None


def percentage_discount_calculator(price_value: float, percent_value: float) -> float:
    """
    Calculate percentage-based discount amount.
    
    Args:
        price_value: Original price value
        percent_value: Percentage for discount
        
    Returns:
        Discount amount calculated
    """
    # Validation with slightly different message
    if percent_value < 0 or percent_value > 100:
        raise ValueError("Percentage value must be in range 0-100")
    
    # Same calculation, different variable names
    discount_amount = price_value * (percent_value / 100)
    return discount_amount