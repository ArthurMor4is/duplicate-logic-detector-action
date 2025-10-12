#!/usr/bin/env python3
"""
Code file with functions that are similar to original_code.py but different enough
to test the sensitivity of the duplicate detection algorithm.
"""

import re
from typing import List, Dict


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format (similar structure to email validation).
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if phone is valid, False otherwise
    """
    # Different regex pattern but similar validation logic
    pattern = r'^\+?1?-?\.?\s?\(?\d{3}\)?-?\.?\s?\d{3}-?\.?\s?\d{4}$'
    return re.match(pattern, phone) is not None


def calculate_markup(cost: float, markup_percentage: float) -> float:
    """
    Calculate markup amount (similar to discount calculation but opposite).
    
    Args:
        cost: Original cost
        markup_percentage: Markup percentage (0-100)
        
    Returns:
        Markup amount
    """
    if markup_percentage < 0:
        raise ValueError("Markup percentage cannot be negative")
    
    return cost * (markup_percentage / 100)


def process_product_data(products: List[Dict]) -> List[Dict]:
    """
    Process and validate product data (similar structure to user processing).
    
    Args:
        products: List of product dictionaries
        
    Returns:
        List of processed product data
    """
    processed_products = []
    
    for product in products:
        if not product.get('name'):
            continue
            
        # Validate product has price
        if not product.get('price') or product['price'] <= 0:
            continue
            
        # Add processed flag
        product['processed'] = True
        product['status'] = 'available'
        
        processed_products.append(product)
    
    return processed_products


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format value as percentage string (different from currency formatting).
    
    Args:
        value: Decimal value to format as percentage
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    percentage = value * 100
    return f"{percentage:.{decimals}f}%"


def parse_yaml_config(config_path: str) -> Dict:
    """
    Parse YAML configuration file (similar to JSON parsing but different format).
    
    Args:
        config_path: Path to YAML config file
        
    Returns:
        Parsed configuration dictionary
    """
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except (FileNotFoundError, ImportError) as e:
        print(f"Error loading YAML config: {e}")
        return {}


def calculate_interest(principal: float, rate: float, time: float) -> float:
    """
    Calculate simple interest (different from tax calculation but similar math).
    
    Args:
        principal: Principal amount
        rate: Interest rate as decimal
        time: Time period
        
    Returns:
        Interest amount
    """
    if rate < 0 or principal < 0 or time < 0:
        raise ValueError("Values cannot be negative")
    
    return principal * rate * time


def filter_available_products(products: List[Dict]) -> List[Dict]:
    """
    Filter list to only include available products (similar to active items).
    
    Args:
        products: List of product dictionaries
        
    Returns:
        List of available products only
    """
    available_products = []
    
    for product in products:
        if product.get('status') == 'available' or product.get('in_stock', False):
            available_products.append(product)
    
    return available_products


def generate_sales_report(sales: List[Dict]) -> Dict:
    """
    Generate summary report for sales (similar structure to user report).
    
    Args:
        sales: List of sales dictionaries
        
    Returns:
        Summary report dictionary
    """
    total_sales = len(sales)
    completed_sales = len([s for s in sales if s.get('status') == 'completed'])
    total_revenue = sum(s.get('amount', 0) for s in sales if s.get('status') == 'completed')
    
    return {
        'total_sales': total_sales,
        'completed_sales': completed_sales,
        'pending_sales': total_sales - completed_sales,
        'completion_rate': completed_sales / total_sales if total_sales > 0 else 0,
        'total_revenue': total_revenue
    }


def validate_url(url: str) -> bool:
    """
    Validate URL format (similar validation pattern to email).
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    url_pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    return re.match(url_pattern, url) is not None


def process_batch_data(data_batch: List[Dict], batch_size: int = 100) -> List[List[Dict]]:
    """
    Process data in batches (different processing approach).
    
    Args:
        data_batch: Data to process in batches
        batch_size: Size of each batch
        
    Returns:
        List of processed batches
    """
    batches = []
    
    for i in range(0, len(data_batch), batch_size):
        batch = data_batch[i:i + batch_size]
        
        # Process each item in the batch
        processed_batch = []
        for item in batch:
            if item.get('valid', True):
                item['batch_processed'] = True
                processed_batch.append(item)
        
        if processed_batch:
            batches.append(processed_batch)
    
    return batches
