from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from firebase_config import firebase_config
from models import user_model
import re
import requests
from datetime import datetime
import os

# Create Blueprint
auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    return True, "Password is valid"

def authenticate_with_firebase(email, password):
    """Authenticate user with Firebase Auth REST API"""
    try:
        # Get Firebase Web API Key from environment
        api_key = os.getenv('FIREBASE_WEB_API_KEY')
        
        if not api_key:
            print("ERROR: FIREBASE_WEB_API_KEY not set in environment variables!")
            print("Get your Web API Key from Firebase Console > Project Settings > General > Web API Key")
            return False, None, "Configuration error"
            
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        print(f"Attempting Firebase authentication for: {email}")
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"Firebase auth response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Firebase authentication successful!")
            return True, data, None
        else:
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', 'Authentication failed')
            
            # Handle specific Firebase error codes
            if 'EMAIL_NOT_FOUND' in error_message:
                return False, None, "No account found with this email address"
            elif 'INVALID_PASSWORD' in error_message:
                return False, None, "Invalid password"
            elif 'USER_DISABLED' in error_message:
                return False, None, "This account has been disabled"
            elif 'TOO_MANY_ATTEMPTS_TRY_LATER' in error_message:
                return False, None, "Too many failed attempts. Please try again later"
            else:
                return False, None, "Invalid email or password"
            
    except requests.exceptions.Timeout:
        print("Firebase auth request timed out")
        return False, None, "Authentication service unavailable. Please try again."
    except requests.exceptions.RequestException as e:
        print(f"Network error during Firebase auth: {e}")
        return False, None, "Network error. Please check your connection and try again."
    except Exception as e:
        print(f"Unexpected error during Firebase auth: {e}")
        return False, None, "An unexpected error occurred. Please try again."

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration with enhanced validation"""
    if request.method == 'POST':
        try:
            # Get form data
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            name = request.form.get('name', '').strip()
            
            # Enhanced validation
            if not all([email, password, confirm_password, name]):
                flash('All fields are required', 'error')
                return render_template('register.html')
            
            if len(name) < 2:
                flash('Name must be at least 2 characters long', 'error')
                return render_template('register.html')
            
            if not validate_email(email):
                flash('Please enter a valid email address', 'error')
                return render_template('register.html')
            
            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return render_template('register.html')
            
            is_valid, message = validate_password(password)
            if not is_valid:
                flash(message, 'error')
                return render_template('register.html')
            
            # Check if user already exists in Firestore
            existing_user = user_model.get_user_by_email(email)
            if existing_user:
                flash('An account with this email already exists', 'error')
                return render_template('register.html')
            
            # Create user in Firebase Auth
            print(f"Creating Firebase Auth user for: {email}")
            firebase_user = firebase_config.create_user(
                email=email,
                password=password,
                display_name=name
            )
            
            print(f"Firebase user created with UID: {firebase_user.uid}")
            
            # Store additional user data in Firestore
            user_data = user_model.create_user(
                uid=firebase_user.uid,
                email=email,
                name=name
            )
            
            print(f"User data stored in Firestore: {user_data}")
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            error_message = str(e).lower()
            print(f"Registration error: {e}")
            
            if 'email-already-exists' in error_message or 'email_already_exists' in error_message:
                flash('An account with this email already exists', 'error')
            elif 'weak-password' in error_message:
                flash('Password is too weak. Please choose a stronger password.', 'error')
            elif 'invalid-email' in error_message:
                flash('Please enter a valid email address', 'error')
            else:
                flash('Registration failed. Please try again.', 'error')
                print(f"Detailed registration error: {e}")
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Enhanced user login with Firebase Auth verification"""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            remember_me = request.form.get('remember_me') == 'on'
            
            print(f"Login attempt for email: {email}")
            
            # Basic validation
            if not email or not password:
                flash('Email and password are required', 'error')
                return render_template('login.html')
            
            if not validate_email(email):
                flash('Please enter a valid email address', 'error')
                return render_template('login.html')
            
            # Authenticate with Firebase
            print("Authenticating with Firebase...")
            is_authenticated, auth_data, error_message = authenticate_with_firebase(email, password)
            
            if not is_authenticated:
                print(f"Authentication failed: {error_message}")
                flash(error_message or 'Invalid email or password', 'error')
                return render_template('login.html')
            
            print("Firebase authentication successful!")
            
            # Get user ID from Firebase auth response
            user_uid = auth_data['localId']
            user_email = auth_data['email']
            id_token = auth_data.get('idToken')
            
            print(f"Authenticated user UID: {user_uid}")
            
            # Get or create user data in Firestore
            user_data = user_model.get_user_by_uid(user_uid)
            if not user_data:
                print("User data not found in Firestore, creating...")
                # Get user details from Firebase Auth
                try:
                    firebase_user = firebase_config.get_user_by_uid(user_uid)
                    display_name = firebase_user.display_name if firebase_user else 'User'
                except:
                    display_name = 'User'
                
                user_data = user_model.create_user(
                    uid=user_uid,
                    email=user_email,
                    name=display_name
                )
            
            # Create secure session
            session.permanent = remember_me
            session['user_id'] = user_data['uid']
            session['user_name'] = user_data['name']
            session['user_email'] = user_data['email']
            session['logged_in'] = True
            session['firebase_token'] = id_token
            session['login_time'] = datetime.now().isoformat()
            
            # Update last login timestamp
            user_model.update_user(user_data['uid'], {
                'last_login': datetime.now(),
                'login_count': user_data.get('login_count', 0) + 1
            })
            
            print(f"Session created for user: {user_data['name']}")
            flash(f'Welcome back, {user_data["name"]}!', 'success')
            
            # Redirect to requested page or dashboard
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):  # Security: only allow relative URLs
                return redirect(next_page)
            
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            print(f"Login error: {e}")
            import traceback
            traceback.print_exc()
            flash('Login failed. Please try again.', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """Enhanced user logout"""
    user_name = session.get('user_name', 'User')
    
    # Clear session
    session.clear()
    
    flash(f'Goodbye, {user_name}! You have been logged out successfully.', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Enhanced forgot password with Firebase Auth REST API"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Email is required', 'error')
            return render_template('forgot_password.html')
        
        if not validate_email(email):
            flash('Please enter a valid email address', 'error')
            return render_template('forgot_password.html')
        
        try:
            api_key = os.getenv('FIREBASE_WEB_API_KEY')
            if not api_key:
                flash('Password reset is currently unavailable. Please contact support.', 'error')
                return render_template('forgot_password.html')
                
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}"
            
            payload = {
                "requestType": "PASSWORD_RESET",
                "email": email
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            # Always show success message for security (don't reveal if email exists)
            flash('If an account with this email exists, you will receive a password reset link shortly.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            print(f"Password reset error: {e}")
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('forgot_password.html')

@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    """Enhanced user profile management"""
    if 'user_id' not in session:
        flash('Please log in to view your profile', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            update_made = False
            
            # Update name
            if name and name != session.get('user_name') and len(name) >= 2:
                user_model.update_user(session['user_id'], {'name': name})
                session['user_name'] = name
                update_made = True
            
            # Update password
            if new_password:
                if new_password != confirm_password:
                    flash('New passwords do not match', 'error')
                elif not current_password:
                    flash('Current password is required to set a new password', 'error')
                else:
                    is_valid, message = validate_password(new_password)
                    if not is_valid:
                        flash(message, 'error')
                    else:
                        # Verify current password
                        email = session.get('user_email')
                        is_authenticated, _, error_msg = authenticate_with_firebase(email, current_password)
                        
                        if not is_authenticated:
                            flash('Current password is incorrect', 'error')
                        else:
                            # Update password in Firebase Auth
                            try:
                                firebase_config.update_user_password(session['user_id'], new_password)
                                flash('Password updated successfully!', 'success')
                                update_made = True
                            except Exception as e:
                                print(f"Password update error: {e}")
                                flash('Error updating password. Please try again.', 'error')
            
            if update_made and 'Password updated' not in [msg[0] for msg in session.get('_flashes', [])]:
                flash('Profile updated successfully!', 'success')
            
        except Exception as e:
            print(f"Profile update error: {e}")
            flash('Error updating profile. Please try again.', 'error')
    
    # Get user data
    user_data = user_model.get_user_by_uid(session['user_id'])
    if not user_data:
        user_data = {
            'name': session.get('user_name', ''),
            'email': session.get('user_email', ''),
            'created_at': datetime.now()
        }
    
    return render_template('profile.html', user=user_data)

@auth_bp.route('/delete-account', methods=['POST'])
def delete_account():
    """Enhanced account deletion"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user_id = session['user_id']
        password = request.json.get('password') if request.is_json else request.form.get('password')
        
        if not password:
            return jsonify({'error': 'Password required for account deletion'}), 400
        
        # Verify password before deletion
        email = session.get('user_email')
        is_authenticated, _, error_msg = authenticate_with_firebase(email, password)
        
        if not is_authenticated:
            return jsonify({'error': 'Invalid password'}), 403
        
        # Delete user trips
        try:
            from models import trip_model
            user_trips = trip_model.get_user_trips(user_id)
            for trip in user_trips:
                trip_model.delete_trip(trip['trip_id'])
        except Exception as e:
            print(f"Error deleting user trips: {e}")
        
        # Delete user from Firestore
        user_model.delete_user(user_id)
        
        # Delete user from Firebase Auth
        firebase_config.delete_user(user_id)
        
        # Clear session
        session.clear()
        
        return jsonify({'success': True, 'message': 'Account deleted successfully'})
        
    except Exception as e:
        print(f"Account deletion error: {e}")
        return jsonify({'error': 'Failed to delete account'}), 500

# Enhanced utility functions
def login_required(f):
    """Decorator for routes that require login with enhanced security"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('logged_in'):
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login', next=request.url))
        
        # Check if session is still valid (optional: add session timeout)
        login_time = session.get('login_time')
        if login_time:
            try:
                login_datetime = datetime.fromisoformat(login_time)
                # Optional: Add session timeout check here
                # if (datetime.now() - login_datetime).total_seconds() > 86400:  # 24 hours
                #     session.clear()
                #     flash('Session expired. Please log in again.', 'error')
                #     return redirect(url_for('auth.login'))
            except:
                pass
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get current user data with caching"""
    if 'user_id' not in session:
        return None
    
    return user_model.get_user_by_uid(session['user_id'])

def verify_session_token():
    """Verify Firebase ID token in session"""
    token = session.get('firebase_token')
    if not token:
        return False
    
    try:
        decoded_token = firebase_config.verify_id_token(token)
        return decoded_token is not None
    except:
        return False