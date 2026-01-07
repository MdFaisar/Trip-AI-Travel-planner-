from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import groq
import firebase_admin
from firebase_admin import credentials, firestore, auth
from pdf_generator import generate_trip_pdf
from prompt import get_trip_plan_prompt
import tempfile
import uuid
from content_formatter import TripContentFormatter
import requests

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Initialize CSRF protection
csrf = CSRFProtect(app)
content_formatter = TripContentFormatter()

# Make csrf_token available to all templates
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate('firebase-service-account-key.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

FIREBASE_WEB_API_KEY = os.getenv('FIREBASE_WEB_API_KEY')
FIREBASE_AUTH_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"

# Initialize Groq client
groq_client = groq.Groq(api_key=os.getenv('GROQ_API_KEY'))

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
    
    # Determine if international trip
    is_international = False
    distance_category = "domestic"
    
    nearby_countries = ["nepal", "bangladesh", "sri lanka", "bhutan", "myanmar"]
    medium_distance = ["thailand", "malaysia", "singapore", "uae", "dubai", "vietnam", "cambodia", "indonesia"]
    far_countries = ["usa", "uk", "france", "germany", "italy", "spain", "australia", "japan", "canada"]
    
    dest_lower = destination.lower()
    
    if any(country in dest_lower for country in nearby_countries):
        is_international = True
        distance_category = "nearby"
    elif any(country in dest_lower for country in medium_distance):
        is_international = True
        distance_category = "medium"
    elif any(country in dest_lower for country in far_countries):
        is_international = True
        distance_category = "far"
    
    if is_international:
        daily_min = base_costs["international"][distance_category]["budget"]
        if distance_category == "nearby":
            transport_cost = 15000
        elif distance_category == "medium":
            transport_cost = 30000
        else:
            transport_cost = 60000
    else:
        daily_min = base_costs["domestic"]["budget"]
        transport_cost = 5000
    
    min_budget = daily_min * num_days + transport_cost
    return min_budget

def get_trip_plan(start_location, destination, num_days, start_date, end_date, budget=None):
    """Generate a trip plan using Llama model through Groq API"""
    prompt = get_trip_plan_prompt(start_location, destination, num_days, start_date, end_date, budget)
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=4000
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error generating trip plan: {str(e)}"

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            name = request.form.get('name', '').strip()
            
            # Basic validation
            if not email or not password or not name:
                flash('All fields are required', 'error')
                return render_template('register.html')
            
            # Check if user already exists
            existing_users = db.collection('users').where('email', '==', email).limit(1).stream()
            if list(existing_users):
                flash('An account with this email already exists', 'error')
                return render_template('register.html')
            
            # Create user in Firebase Auth
            user = auth.create_user(
                email=email,
                email_verified=False,
                password=password,
                display_name=name,
                disabled=False
            )
            
            # Store additional user data in Firestore
            user_data = {
                'uid': user.uid,
                'email': email,
                'name': name,
                'created_at': datetime.now(),
                'profile_picture': '',
                'preferences': {
                    'currency': 'INR',
                    'language': 'en',
                    'notifications': True
                }
            }
            
            db.collection('users').document(user.uid).set(user_data)
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            error_message = str(e)
            if 'email-already-exists' in error_message:
                flash('An account with this email already exists', 'error')
            elif 'weak-password' in error_message:
                flash('Password must be at least 6 characters long', 'error')
            elif 'invalid-email' in error_message:
                flash('Please enter a valid email address', 'error')
            else:
                flash(f'Registration failed: {error_message}', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login using Firebase Auth REST API"""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            # Basic validation
            if not email or not password:
                flash('Email and password are required', 'error')
                return render_template('login.html')
            
            # Authenticate with Firebase Auth REST API
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(FIREBASE_AUTH_URL, json=payload)
            
            if response.status_code == 200:
                user_data = response.json()
                id_token = user_data['idToken']
                
                # Verify the ID token with Firebase Admin SDK
                decoded_token = auth.verify_id_token(id_token)
                uid = decoded_token['uid']
                
                # Get additional user data from Firestore
                user_doc = db.collection('users').document(uid).get()
                
                if user_doc.exists:
                    firestore_user_data = user_doc.to_dict()
                    
                    # Create session
                    session['user_id'] = uid
                    session['user_name'] = firestore_user_data['name']
                    session['user_email'] = firestore_user_data['email']
                    session['logged_in'] = True
                    session['id_token'] = id_token  # Store for API calls
                    
                    # Update last login
                    db.collection('users').document(uid).update({
                        'last_login': datetime.now()
                    })
                    
                    flash('Logged in successfully!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('User profile not found', 'error')
            else:
                # Handle authentication errors
                error_data = response.json()
                error_message = error_data.get('error', {}).get('message', '')
                
                if 'INVALID_LOGIN_CREDENTIALS' in error_message:
                    flash('Invalid email or password', 'error')
                elif 'EMAIL_NOT_FOUND' in error_message:
                    flash('No account found with this email address', 'error')
                elif 'INVALID_PASSWORD' in error_message:
                    flash('Invalid email or password', 'error')
                elif 'TOO_MANY_ATTEMPTS_TRY_LATER' in error_message:
                    flash('Too many failed login attempts. Please try again later.', 'error')
                elif 'USER_DISABLED' in error_message:
                    flash('This account has been disabled', 'error')
                else:
                    flash('Login failed. Please check your credentials.', 'error')
                
        except requests.exceptions.RequestException as e:
            flash('Network error. Please try again.', 'error')
        except Exception as e:
            flash('Login failed. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        flash('Please log in to access the dashboard', 'error')
        return redirect(url_for('login'))
    
    # Get user's trips
    trips_ref = db.collection('trips').where('user_id', '==', session['user_id']).order_by('created_at', direction=firestore.Query.DESCENDING)
    trips = [trip.to_dict() for trip in trips_ref.stream()]
    
    return render_template('dashboard.html', trips=trips)

@app.route('/trip_planner')
def trip_planner():
    """Trip planning form"""
    if 'user_id' not in session:
        flash('Please log in to plan a trip', 'error')
        return redirect(url_for('login'))
    
    return render_template('trip_planner.html')

@app.route('/generate_trip', methods=['POST'])
def generate_trip():
    """Generate trip plan"""
    if 'user_id' not in session:
        return jsonify({'error': 'Please log in first'}), 401
    
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.json
        else:
            data = request.form.to_dict()
            
        start_location = data.get('start_location')
        destination = data.get('destination')
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        
        # Fix: Handle empty budget_amount safely
        budget_amount_str = data.get('budget_amount', '0')
        if budget_amount_str == '' or budget_amount_str is None:
            budget_amount = 0.0
        else:
            try:
                budget_amount = float(budget_amount_str)
            except (ValueError, TypeError):
                budget_amount = 0.0
        
        currency = data.get('currency', 'INR')
        
        num_days = (end_date - start_date).days + 1
        
        # Currency symbols
        currency_symbols = {
            "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥",
            "AUD": "A$", "CAD": "C$", "INR": "₹", "CNY": "¥"
        }
        
        budget = {
            "amount": budget_amount,
            "currency": currency,
            "symbol": currency_symbols.get(currency, "$")
        }
        
        # Generate trip plan
        trip_plan = get_trip_plan(start_location, destination, num_days, start_date, end_date, budget)
        formatted_trip_plan = content_formatter.format_for_web(trip_plan)

        trip_summary = content_formatter.extract_summary(trip_plan)
        day_wise_content = content_formatter.get_day_wise_content(trip_plan)
        highlights = content_formatter.get_highlights(trip_plan)

        # Save trip to database
        trip_id = str(uuid.uuid4())
        trip_data = {
            'trip_id': trip_id,
            'user_id': session['user_id'],
            'title': f"{start_location} to {destination}",
            'start_location': start_location,
            'destination': destination,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'duration': num_days,
            'budget': budget,
            'trip_plan': trip_plan,
            'formatted_trip_plan': formatted_trip_plan,
            'summary': trip_summary,
            'highlights': highlights,
            'created_at': datetime.now(),
            'status': 'completed'
        }
        
        db.collection('trips').document(trip_id).set(trip_data)
        
        # Fixed: Pass trip_data as 'trip' to match the template expectation
        if request.is_json:
            return jsonify({
                'success': True,
                'trip_id': trip_data['trip_id'],
                'trip_plan': trip_plan
            })
        else:
            # Return HTML template like in app.py
            return render_template('trip_result.html',
                                 trip_id=trip_data['trip_id'],
                                 trip=trip_data,
                                 formatted_content=formatted_trip_plan,
                                 day_wise_content=day_wise_content,
                                 highlights=highlights)
        
    except Exception as e:
        flash(f'Error generating trip plan: {str(e)}', 'error')
        return jsonify({'error': str(e)}), 500

@app.route('/trip/<trip_id>')
def view_trip(trip_id):
    """View specific trip"""
    if 'user_id' not in session:
        flash('Please log in to view trips', 'error')
        return redirect(url_for('login'))
    
    # Get trip from database
    trip_ref = db.collection('trips').document(trip_id)
    trip = trip_ref.get()
    
    if not trip.exists:
        flash('Trip not found', 'error')
        return redirect(url_for('dashboard'))
    
    trip_data = trip.to_dict()
    
    # Check if user owns this trip
    if trip_data.get('user_id') != session['user_id']:
        flash('Access denied', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('trip_result.html', trip=trip_data)

@app.route('/download_pdf/<trip_id>')
def download_pdf(trip_id):
    """Download trip plan as PDF"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get trip from database
    trip_ref = db.collection('trips').document(trip_id)
    trip = trip_ref.get()
    
    if not trip.exists or trip.to_dict().get('user_id') != session['user_id']:
        flash('Trip not found or access denied', 'error')
        return redirect(url_for('dashboard'))
    
    trip_data = trip.to_dict()
    
    # Generate PDF
    start_date = datetime.strptime(trip_data['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(trip_data['end_date'], '%Y-%m-%d').date()
    
    pdf_path = generate_trip_pdf(
        trip_data['trip_plan'],
        trip_data['start_location'],
        trip_data['destination'],
        start_date,
        end_date
    )
    
    filename = f"trip_plan_{trip_data['start_location']}_to_{trip_data['destination']}_{start_date}.pdf"
    
    return send_file(pdf_path, as_attachment=True, download_name=filename, mimetype='application/pdf')

@app.route('/profile')
def profile():
    """User profile page"""
    if 'user_id' not in session:
        flash('Please log in to view profile', 'error')
        return redirect(url_for('login'))
    
    # Get user data
    user_ref = db.collection('users').document(session['user_id'])
    user = user_ref.get()
    
    if user.exists:
        user_data = user.to_dict()
    else:
        user_data = {
            'name': session.get('user_name', ''),
            'email': session.get('user_email', '')
        }
    
    # Get trip statistics
    trips_ref = db.collection('trips').where('user_id', '==', session['user_id'])
    trips_count = len(list(trips_ref.stream()))
    
    return render_template('profile.html', user=user_data, trips_count=trips_count)

@app.route('/api/calculate_min_budget')
def api_calculate_min_budget():
    """API endpoint to calculate minimum budget"""
    start_location = request.args.get('start_location', '')
    destination = request.args.get('destination', '')
    num_days = int(request.args.get('num_days', 1))
    
    min_budget = calculate_min_budget(start_location, destination, num_days)
    
    return jsonify({'min_budget': min_budget})

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors"""
    if 'CSRF' in str(error):
        flash('Security token expired. Please try again.', 'error')
        return redirect(request.referrer or url_for('index'))
    return render_template('error.html', error="Bad Request"), 400


if __name__ == '__main__':

    app.run()
