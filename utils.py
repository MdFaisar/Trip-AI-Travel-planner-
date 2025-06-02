import re
import os
import secrets
import string
from datetime import datetime, timedelta
from functools import wraps
from flask import session, flash, redirect, url_for, request
import hashlib
import json
from typing import Dict, List, Optional, Any

def login_required(f):
    """Decorator to require login for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def generate_secure_token(length=32):
    """Generate a secure random token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"

def sanitize_input(text):
    """Sanitize user input to prevent XSS"""
    if not text:
        return ""
    
    # Remove potential HTML tags
    text = re.sub(r'<[^>]+>', '', str(text))
    
    # Remove or escape special characters
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    
    return text.strip()

def validate_date_range(start_date_str, end_date_str):
    """Validate date range for trip planning"""
    try:
        if isinstance(start_date_str, str):
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = start_date_str
            
        if isinstance(end_date_str, str):
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = end_date_str
        
        today = datetime.now().date()
        
        # Check if start date is in the future
        if start_date < today:
            return False, "Start date cannot be in the past"
        
        # Check if end date is after start date
        if end_date <= start_date:
            return False, "End date must be after start date"
        
        # Check if trip duration is reasonable (max 1 year)
        if (end_date - start_date).days > 365:
            return False, "Trip duration cannot exceed 1 year"
        
        return True, "Date range is valid"
    
    except ValueError:
        return False, "Invalid date format. Please use YYYY-MM-DD"

def calculate_trip_duration(start_date, end_date):
    """Calculate trip duration in days"""
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    return (end_date - start_date).days + 1

def format_currency(amount, currency='INR', symbol='₹'):
    """Format currency amount"""
    try:
        amount = float(amount)
        if currency == 'INR':
            # Indian number format (lakhs and crores)
            if amount >= 10000000:  # 1 crore
                return f"{symbol}{amount/10000000:.1f} Cr"
            elif amount >= 100000:  # 1 lakh
                return f"{symbol}{amount/100000:.1f} L"
            else:
                return f"{symbol}{amount:,.0f}"
        else:
            # Standard international format
            return f"{symbol}{amount:,.2f}"
    except (ValueError, TypeError):
        return f"{symbol}0"

def get_currency_info(currency_code):
    """Get currency information"""
    currencies = {
        'USD': {'name': 'US Dollar', 'symbol': '$', 'rate': 83.0},
        'EUR': {'name': 'Euro', 'symbol': '€', 'rate': 90.0},
        'GBP': {'name': 'British Pound', 'symbol': '£', 'rate': 105.0},
        'JPY': {'name': 'Japanese Yen', 'symbol': '¥', 'rate': 0.56},
        'AUD': {'name': 'Australian Dollar', 'symbol': 'A$', 'rate': 55.0},
        'CAD': {'name': 'Canadian Dollar', 'symbol': 'C$', 'rate': 62.0},
        'INR': {'name': 'Indian Rupee', 'symbol': '₹', 'rate': 1.0},
        'CNY': {'name': 'Chinese Yuan', 'symbol': '¥', 'rate': 11.5},
    }
    
    return currencies.get(currency_code, currencies['INR'])

def classify_destination_type(destination):
    """Classify destination as domestic or international and get distance category"""
    destination_lower = destination.lower()
    
    # Indian cities/states (domestic)
    indian_locations = [
        'mumbai', 'delhi', 'bangalore', 'chennai', 'kolkata', 'hyderabad',
        'pune', 'ahmedabad', 'surat', 'jaipur', 'lucknow', 'kanpur',
        'nagpur', 'indore', 'thane', 'bhopal', 'visakhapatnam', 'pimpri',
        'patna', 'vadodara', 'ghaziabad', 'ludhiana', 'agra', 'nashik',
        'kerala', 'goa', 'rajasthan', 'himachal', 'uttarakhand', 'kashmir',
        'punjab', 'haryana', 'gujarat', 'maharashtra', 'karnataka',
        'tamil nadu', 'andhra pradesh', 'telangana', 'odisha', 'bihar',
        'coimbatore', 'madurai', 'salem', 'tiruchirappalli', 'tirunelveli'
    ]
    
    # Nearby countries
    nearby_countries = [
        'nepal', 'bangladesh', 'sri lanka', 'bhutan', 'myanmar', 'maldives',
        'afghanistan', 'pakistan'
    ]
    
    # Medium distance countries
    medium_distance = [
        'thailand', 'malaysia', 'singapore', 'uae', 'dubai', 'vietnam',
        'cambodia', 'indonesia', 'philippines', 'china', 'japan', 'south korea',
        'taiwan', 'hong kong', 'macau', 'oman', 'qatar', 'kuwait', 'bahrain'
    ]
    
    # Far countries
    far_countries = [
        'usa', 'uk', 'france', 'germany', 'italy', 'spain', 'australia',
        'canada', 'brazil', 'argentina', 'russia', 'turkey', 'egypt',
        'south africa', 'netherlands', 'switzerland', 'sweden', 'norway'
    ]
    
    # Check destination type
    if any(location in destination_lower for location in indian_locations):
        return {'type': 'domestic', 'category': 'domestic'}
    elif any(country in destination_lower for country in nearby_countries):
        return {'type': 'international', 'category': 'nearby'}
    elif any(country in destination_lower for country in medium_distance):
        return {'type': 'international', 'category': 'medium'}
    elif any(country in destination_lower for country in far_countries):
        return {'type': 'international', 'category': 'far'}
    else:
        # Default to domestic if not recognized
        return {'type': 'domestic', 'category': 'domestic'}

def calculate_min_budget(start_location, destination, num_days):
    """Calculate minimum budget based on location and duration"""
    base_costs = {
        "domestic": {
            "budget": 2000,
            "mid": 5000,
            "luxury": 10000
        },
        "international": {
            "nearby": {
                "budget": 5000,
                "mid": 10000,
                "luxury": 20000
            },
            "medium": {
                "budget": 8000,
                "mid": 15000,
                "luxury": 30000
            },
            "far": {
                "budget": 12000,
                "mid": 25000,
                "luxury": 50000
            }
        }
    }
    
    destination_info = classify_destination_type(destination)
    
    if destination_info['type'] == 'international':
        daily_min = base_costs["international"][destination_info['category']]["budget"]
        if destination_info['category'] == "nearby":
            transport_cost = 15000
        elif destination_info['category'] == "medium":
            transport_cost = 30000
        else:
            transport_cost = 60000
    else:
        daily_min = base_costs["domestic"]["budget"]
        transport_cost = 5000
    
    min_budget = daily_min * num_days + transport_cost
    return min_budget

def generate_trip_id():
    """Generate unique trip ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = secrets.token_hex(4)
    return f"trip_{timestamp}_{random_suffix}"

def format_trip_title(start_location, destination):
    """Format trip title"""
    start = start_location.title()
    dest = destination.title()
    return f"{start} to {dest}"

def validate_budget(budget_amount, currency='INR'):
    """Validate budget amount"""
    try:
        amount = float(budget_amount)
        if amount <= 0:
            return False, "Budget must be greater than 0"
        
        # Set reasonable limits based on currency
        limits = {
            'INR': {'min': 1000, 'max': 10000000},
            'USD': {'min': 10, 'max': 100000},
            'EUR': {'min': 10, 'max': 100000},
            'GBP': {'min': 10, 'max': 100000}
        }
        
        limit = limits.get(currency, limits['INR'])
        
        if amount < limit['min']:
            return False, f"Budget too low. Minimum: {limit['min']} {currency}"
        
        if amount > limit['max']:
            return False, f"Budget too high. Maximum: {limit['max']} {currency}"
        
        return True, "Budget is valid"
    
    except (ValueError, TypeError):
        return False, "Invalid budget amount"

def clean_trip_plan_text(text):
    """Clean and format trip plan text"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    # Fix common formatting issues
    text = re.sub(r'(\w)\*(\w)', r'\1 \2', text)  # Fix merged words with asterisks
    text = re.sub(r'\*{3,}', '**', text)  # Reduce multiple asterisks
    
    # Ensure proper spacing around headings
    text = re.sub(r'(^|\n)([A-Z\s]+:)\s*', r'\1\n\2\n', text, flags=re.MULTILINE)
    
    return text.strip()

def get_user_agent():
    """Get user agent string"""
    return request.headers.get('User-Agent', '')

def get_client_ip():
    """Get client IP address"""
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
    elif request.environ.get('HTTP_X_REAL_IP'):
        return request.environ['HTTP_X_REAL_IP']
    else:
        return request.environ.get('REMOTE_ADDR', 'Unknown')

def log_user_activity(user_id, action, details=None):
    """Log user activity (for analytics)"""
    activity = {
        'user_id': user_id,
        'action': action,
        'details': details or {},
        'timestamp': datetime.now().isoformat(),
        'ip_address': get_client_ip(),
        'user_agent': get_user_agent()
    }
    
    # In a production app, you might want to store this in a database
    # For now, we'll just return the activity log
    return activity

def create_error_response(message, status_code=400):
    """Create standardized error response"""
    return {
        'success': False,
        'error': message,
        'timestamp': datetime.now().isoformat()
    }, status_code

def create_success_response(data=None, message="Success"):
    """Create standardized success response"""
    response = {
        'success': True,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    
    if data:
        response['data'] = data
    
    return response

def truncate_text(text, max_length=100, suffix="..."):
    """Truncate text to specified length"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def safe_get(dictionary, key, default=None):
    """Safely get value from dictionary"""
    try:
        return dictionary.get(key, default)
    except (AttributeError, TypeError):
        return default

def format_date_for_display(date_obj):
    """Format date for display"""
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        except ValueError:
            return date_obj
    
    if hasattr(date_obj, 'strftime'):
        return date_obj.strftime('%B %d, %Y')
    
    return str(date_obj)

def get_time_ago(timestamp):
    """Get human-readable time ago string"""
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            return "Unknown time"
    
    now = datetime.now()
    if timestamp.tzinfo:
        now = datetime.now(timestamp.tzinfo)
    
    diff = now - timestamp
    
    if diff.days > 7:
        return timestamp.strftime('%B %d, %Y')
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

def validate_location(location):
    """Validate location input"""
    if not location or not location.strip():
        return False, "Location cannot be empty"
    
    location = location.strip()
    
    if len(location) < 2:
        return False, "Location must be at least 2 characters long"
    
    if len(location) > 100:
        return False, "Location cannot exceed 100 characters"
    
    # Check for valid characters (letters, numbers, spaces, common punctuation)
    if not re.match(r'^[a-zA-Z0-9\s,.\-\'()]+$', location):
        return False, "Location contains invalid characters"
    
    return True, "Location is valid"

def extract_numbers_from_text(text):
    """Extract numbers from text"""
    if not text:
        return []
    
    numbers = re.findall(r'\d+(?:\.\d+)?', str(text))
    return [float(num) if '.' in num else int(num) for num in numbers]

def get_season_from_date(date_obj):
    """Get season from date"""
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
        except ValueError:
            return "Unknown"
    
    month = date_obj.month
    
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    else:
        return "Autumn"

def generate_filename(prefix, extension, include_timestamp=True):
    """Generate filename with optional timestamp"""
    if include_timestamp:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{timestamp}.{extension}"
    else:
        return f"{prefix}.{extension}"

def parse_duration_string(duration_str):
    """Parse duration string like '5 days', '2 weeks', etc."""
    if not duration_str:
        return 0
    
    duration_str = duration_str.lower().strip()
    
    # Extract number and unit
    match = re.match(r'(\d+)\s*(day|days|week|weeks|month|months|year|years)?', duration_str)
    
    if not match:
        return 0
    
    number = int(match.group(1))
    unit = match.group(2) or 'days'
    
    # Convert to days
    if 'day' in unit:
        return number
    elif 'week' in unit:
        return number * 7
    elif 'month' in unit:
        return number * 30
    elif 'year' in unit:
        return number * 365
    
    return number

def compress_json(data):
    """Compress JSON data for storage"""
    import json
    import gzip
    import base64
    
    json_str = json.dumps(data)
    compressed = gzip.compress(json_str.encode('utf-8'))
    return base64.b64encode(compressed).decode('ascii')

def decompress_json(compressed_data):
    """Decompress JSON data"""
    import json
    import gzip
    import base64
    
    try:
        compressed = base64.b64decode(compressed_data.encode('ascii'))
        decompressed = gzip.decompress(compressed)
        return json.loads(decompressed.decode('utf-8'))
    except Exception:
        return None

def get_trip_statistics(trips):
    """Calculate trip statistics"""
    if not trips:
        return {
            'total_trips': 0,
            'total_days': 0,
            'countries_visited': 0,
            'domestic_trips': 0,
            'international_trips': 0,
            'average_duration': 0,
            'total_budget': 0
        }
    
    total_trips = len(trips)
    total_days = 0
    countries = set()
    domestic_count = 0
    international_count = 0
    total_budget = 0
    
    for trip in trips:
        # Calculate days
        if 'duration' in trip:
            total_days += trip['duration']
        
        # Count countries/destinations
        destination = trip.get('destination', '').lower()
        countries.add(destination)
        
        # Classify trip type
        dest_info = classify_destination_type(destination)
        if dest_info['type'] == 'domestic':
            domestic_count += 1
        else:
            international_count += 1
        
        # Sum budget
        budget = trip.get('budget', {})
        if isinstance(budget, dict) and 'amount' in budget:
            # Convert to INR for comparison (simplified)
            amount = budget['amount']
            currency = budget.get('currency', 'INR')
            
            if currency != 'INR':
                currency_info = get_currency_info(currency)
                amount = amount * currency_info['rate']
            
            total_budget += amount
    
    average_duration = total_days / total_trips if total_trips > 0 else 0
    
    return {
        'total_trips': total_trips,
        'total_days': total_days,
        'countries_visited': len(countries),
        'domestic_trips': domestic_count,
        'international_trips': international_count,
        'average_duration': round(average_duration, 1),
        'total_budget': total_budget
    }

def generate_trip_suggestions(user_trips, preferences=None):
    """Generate trip suggestions based on user history"""
    if not user_trips:
        # Default suggestions for new users
        return [
            {'destination': 'Goa', 'type': 'Beach', 'duration': '4-5 days'},
            {'destination': 'Kerala', 'type': 'Backwaters', 'duration': '6-7 days'},
            {'destination': 'Rajasthan', 'type': 'Heritage', 'duration': '8-10 days'},
            {'destination': 'Himachal Pradesh', 'type': 'Mountains', 'duration': '5-6 days'},
            {'destination': 'Thailand', 'type': 'International', 'duration': '7-8 days'}
        ]
    
    # Analyze user's trip patterns
    visited_destinations = [trip.get('destination', '').lower() for trip in user_trips]
    avg_duration = sum(trip.get('duration', 0) for trip in user_trips) / len(user_trips)
    
    # Generate suggestions based on patterns
    suggestions = []
    
    # Suggest similar duration trips
    if avg_duration <= 3:
        suggestions.extend([
            {'destination': 'Pondicherry', 'type': 'Weekend Getaway', 'duration': '2-3 days'},
            {'destination': 'Lonavala', 'type': 'Hill Station', 'duration': '2-3 days'}
        ])
    elif avg_duration <= 7:
        suggestions.extend([
            {'destination': 'Kashmir', 'type': 'Mountains', 'duration': '6-7 days'},
            {'destination': 'Andaman', 'type': 'Islands', 'duration': '5-6 days'}
        ])
    else:
        suggestions.extend([
            {'destination': 'Europe', 'type': 'Multi-country', 'duration': '10-14 days'},
            {'destination': 'Japan', 'type': 'Cultural', 'duration': '8-10 days'}
        ])
    
    return suggestions[:5]

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    """Verify password against hash"""
    return hash_password(password) == hashed_password

def generate_user_id():
    """Generate unique user ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = secrets.token_hex(6)
    return f"user_{timestamp}_{random_suffix}"

def is_valid_trip_data(trip_data):
    """Validate trip data structure"""
    required_fields = ['start_location', 'destination', 'start_date', 'end_date', 'budget']
    
    if not isinstance(trip_data, dict):
        return False, "Trip data must be a dictionary"
    
    for field in required_fields:
        if field not in trip_data:
            return False, f"Missing required field: {field}"
    
    return True, "Trip data is valid"

def format_trip_data_for_storage(trip_data):
    """Format trip data for Firebase storage"""
    formatted_data = {
        'trip_id': trip_data.get('trip_id', generate_trip_id()),
        'user_id': trip_data.get('user_id'),
        'start_location': sanitize_input(trip_data.get('start_location', '')),
        'destination': sanitize_input(trip_data.get('destination', '')),
        'start_date': trip_data.get('start_date'),
        'end_date': trip_data.get('end_date'),
        'duration': calculate_trip_duration(trip_data.get('start_date'), trip_data.get('end_date')),
        'budget': {
            'amount': float(trip_data.get('budget', {}).get('amount', 0)),
            'currency': trip_data.get('budget', {}).get('currency', 'INR')
        },
        'interests': trip_data.get('interests', []),
        'trip_plan': clean_trip_plan_text(trip_data.get('trip_plan', '')),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'status': 'active'
    }
    
    return formatted_data