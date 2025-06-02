from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from datetime import datetime, timedelta
from models import trip_model, user_model
from auth import login_required, get_current_user
from pdf_generator import generate_trip_pdf
from prompt import get_trip_plan_prompt
from content_formatter import TripContentFormatter  # Add this import
import uuid
import tempfile
import os
import groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client
groq_client = groq.Groq(api_key=os.getenv('GROQ_API_KEY'))

# Create Blueprint
main_bp = Blueprint('main', __name__)
content_formatter = TripContentFormatter()

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

@main_bp.route('/')
def index():
    """Home page"""
    # Get user data if logged in
    user = get_current_user() if 'user_id' in session else None
    
    # Get some sample destinations or featured trips
    featured_destinations = [
        {'name': 'Goa', 'image': 'goa.jpg', 'description': 'Beautiful beaches and nightlife'},
        {'name': 'Kerala', 'image': 'kerala.jpg', 'description': 'God\'s own country'},
        {'name': 'Rajasthan', 'image': 'rajasthan.jpg', 'description': 'Royal heritage and culture'},
        {'name': 'Himachal Pradesh', 'image': 'himachal.jpg', 'description': 'Mountains and adventure'}
    ]
    
    return render_template('index.html', user=user, featured_destinations=featured_destinations)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    try:
        user_id = session['user_id']
        
        # Get user trips
        trips = trip_model.get_user_trips(user_id, limit=10)
        
        # Get trip statistics
        stats = trip_model.get_trip_statistics(user_id)
        
        # Get recent trips
        recent_trips = trips[:5] if trips else []
        
        # Get favorite trips
        favorite_trips = [trip for trip in trips if trip.get('is_favorite', False)][:3]
        
        # Calculate upcoming trips
        upcoming_trips = []
        today = datetime.now().date()
        
        for trip in trips:
            if trip.get('start_date'):
                try:
                    start_date = datetime.fromisoformat(trip['start_date']).date()
                    if start_date >= today:
                        upcoming_trips.append(trip)
                except:
                    pass
        
        upcoming_trips.sort(key=lambda x: x.get('start_date', ''))
        upcoming_trips = upcoming_trips[:3]
        
        dashboard_data = {
            'trips': trips,
            'stats': stats,
            'recent_trips': recent_trips,
            'favorite_trips': favorite_trips,
            'upcoming_trips': upcoming_trips
        }
        
        return render_template('dashboard.html', **dashboard_data)
        
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', trips=[], stats={})

@main_bp.route('/trip-planner')
@login_required
def trip_planner():
    """Trip planning form"""
    return render_template('trip_planner.html')

@main_bp.route('/generate-trip', methods=['POST'])
@login_required
def generate_trip():
    """Generate trip plan"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.json
        else:
            data = request.form.to_dict()
        
        # Validate input data
        required_fields = ['start_location', 'destination', 'start_date', 'end_date']
        for field in required_fields:
            if not data.get(field):
                if request.is_json:
                    return jsonify({'error': f'{field} is required'}), 400
                else:
                    flash(f'{field} is required', 'error')
                    return redirect(url_for('main.trip_planner'))
        
        start_location = data.get('start_location').strip()
        destination = data.get('destination').strip()
        start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()
        budget_amount = float(data.get('budget_amount', 0))
        currency = data.get('currency', 'INR')
        
        # Validate dates
        if end_date <= start_date:
            error_msg = 'End date must be after start date'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return redirect(url_for('main.trip_planner'))
        
        if start_date < datetime.now().date():
            error_msg = 'Start date cannot be in the past'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return redirect(url_for('main.trip_planner'))
        
        num_days = (end_date - start_date).days + 1
        
        # Validate trip duration
        if num_days > 30:
            error_msg = 'Trip duration cannot exceed 30 days'
            if request.is_json:
                return jsonify({'error': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return redirect(url_for('main.trip_planner'))
        
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
        
        # Generate trip plan using AI
        trip_plan = get_trip_plan(start_location, destination, num_days, start_date, end_date, budget)
        
        if trip_plan.startswith("Error"):
            if request.is_json:
                return jsonify({'error': trip_plan}), 500
            else:
                flash(trip_plan, 'error')
                return redirect(url_for('main.trip_planner'))
        
        # Format the trip content
        formatted_trip_plan = content_formatter.format_for_web(trip_plan)
        trip_summary = content_formatter.extract_summary(trip_plan)
        day_wise_content = content_formatter.get_day_wise_content(trip_plan)
        highlights = content_formatter.get_highlights(trip_plan)
        
        # Create trip in database
        title = f"{start_location} to {destination}"
        trip_data = {
            'trip_id': str(uuid.uuid4()),
            'user_id': session['user_id'],
            'title': title,
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
        
        # Save to database using trip_model
        saved_trip = trip_model.create_trip(
            user_id=session['user_id'],
            title=title,
            start_location=start_location,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            trip_plan=trip_plan
        )
        
        # Update the trip_data with the saved trip ID
        trip_data['trip_id'] = saved_trip['trip_id']
        
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
        
    except ValueError as e:
        error_msg = 'Invalid date format'
        if request.is_json:
            return jsonify({'error': error_msg}), 400
        else:
            flash(error_msg, 'error')
            return redirect(url_for('main.trip_planner'))
    except Exception as e:
        error_msg = f'Error generating trip plan: {str(e)}'
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        else:
            flash(error_msg, 'error')
            return redirect(url_for('main.trip_planner'))

@main_bp.route('/trip/<trip_id>')
@login_required
def view_trip(trip_id):
    """View specific trip"""
    try:
        trip = trip_model.get_trip_by_id(trip_id)
        
        if not trip:
            flash('Trip not found', 'error')
            return redirect(url_for('main.dashboard'))
        
        # Check if user owns this trip
        if trip.get('user_id') != session['user_id']:
            flash('Access denied', 'error')
            return redirect(url_for('main.dashboard'))
        
        # Convert date strings back to date objects for display
        if trip.get('start_date'):
            trip['start_date_obj'] = datetime.fromisoformat(trip['start_date']).date()
        if trip.get('end_date'):
            trip['end_date_obj'] = datetime.fromisoformat(trip['end_date']).date()
        
        return render_template('trip_result.html', trip=trip)
        
    except Exception as e:
        flash(f'Error loading trip: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/trip/<trip_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_trip(trip_id):
    """Edit trip details"""
    try:
        trip = trip_model.get_trip_by_id(trip_id)
        
        if not trip or trip.get('user_id') != session['user_id']:
            flash('Trip not found or access denied', 'error')
            return redirect(url_for('main.dashboard'))
        
        if request.method == 'POST':
            data = request.get_json()
            
            update_data = {}
            if data.get('title'):
                update_data['title'] = data['title'].strip()
            if data.get('notes'):
                update_data['notes'] = data['notes'].strip()
            if 'tags' in data:
                update_data['tags'] = [tag.strip() for tag in data['tags'] if tag.strip()]
            
            if update_data:
                trip_model.update_trip(trip_id, update_data)
                return jsonify({'success': True})
            
            return jsonify({'error': 'No data to update'}), 400
        
        return render_template('edit_trip.html', trip=trip)
        
    except Exception as e:
        flash(f'Error editing trip: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/trip/<trip_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(trip_id):
    """Toggle trip favorite status"""
    try:
        trip = trip_model.get_trip_by_id(trip_id)
        
        if not trip or trip.get('user_id') != session['user_id']:
            return jsonify({'error': 'Trip not found or access denied'}), 404
        
        is_favorite = not trip.get('is_favorite', False)
        trip_model.mark_favorite(trip_id, is_favorite)
        
        return jsonify({
            'success': True,
            'is_favorite': is_favorite
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/trip/<trip_id>/delete', methods=['POST'])
@login_required
def delete_trip(trip_id):
    """Delete trip"""
    try:
        trip = trip_model.get_trip_by_id(trip_id)
        
        if not trip or trip.get('user_id') != session['user_id']:
            return jsonify({'error': 'Trip not found or access denied'}), 404
        
        trip_model.delete_trip(trip_id)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/download-pdf/<trip_id>')
@login_required
def download_pdf(trip_id):
    """Download trip plan as PDF"""
    try:
        trip = trip_model.get_trip_by_id(trip_id)
        
        if not trip or trip.get('user_id') != session['user_id']:
            flash('Trip not found or access denied', 'error')
            return redirect(url_for('main.dashboard'))
        
        # Convert date strings to date objects
        start_date = datetime.fromisoformat(trip['start_date']).date()
        end_date = datetime.fromisoformat(trip['end_date']).date()
        
        # Generate PDF
        pdf_path = generate_trip_pdf(
            trip['trip_plan'],
            trip['start_location'],
            trip['destination'],
            start_date,
            end_date
        )
        
        filename = f"trip_plan_{trip['start_location']}_to_{trip['destination']}_{start_date}.pdf"
        filename = filename.replace(' ', '_').replace(',', '')
        
        return send_file(
            pdf_path, 
            as_attachment=True, 
            download_name=filename, 
            mimetype='application/pdf'
        )
        
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('main.view_trip', trip_id=trip_id))

@main_bp.route('/api/calculate-min-budget')
def api_calculate_min_budget():
    """API endpoint to calculate minimum budget"""
    try:
        start_location = request.args.get('start_location', '').strip()
        destination = request.args.get('destination', '').strip()
        num_days = int(request.args.get('num_days', 1))
        
        if not start_location or not destination:
            return jsonify({'error': 'Start location and destination are required'}), 400
        
        if num_days < 1 or num_days > 30:
            return jsonify({'error': 'Number of days must be between 1 and 30'}), 400
        
        min_budget = calculate_min_budget(start_location, destination, num_days)
        
        return jsonify({'min_budget': min_budget})
        
    except ValueError:
        return jsonify({'error': 'Invalid number of days'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/trips')
@login_required
def trips_list():
    """List all user trips with filtering and pagination"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        status = request.args.get('status')
        search = request.args.get('search', '').strip()
        
        user_id = session['user_id']
        
        # Get trips
        trips = trip_model.get_user_trips(user_id, limit=100, status=status)
        
        # Filter by search term
        if search:
            trips = [
                trip for trip in trips 
                if search.lower() in trip.get('title', '').lower() or 
                   search.lower() in trip.get('destination', '').lower() or
                   search.lower() in trip.get('start_location', '').lower()
            ]
        
        # Pagination
        total_trips = len(trips)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        trips_page = trips[start_idx:end_idx]
        
        # Calculate pagination info
        total_pages = (total_trips + limit - 1) // limit
        has_prev = page > 1
        has_next = page < total_pages
        
        pagination = {
            'page': page,
            'limit': limit,
            'total_trips': total_trips,
            'total_pages': total_pages,
            'has_prev': has_prev,
            'has_next': has_next,
            'prev_page': page - 1 if has_prev else None,
            'next_page': page + 1 if has_next else None
        }
        
        return render_template('trips_list.html', 
                             trips=trips_page, 
                             pagination=pagination,
                             current_status=status,
                             search_term=search)
        
    except Exception as e:
        flash(f'Error loading trips: {str(e)}', 'error')
        return render_template('trips_list.html', trips=[], pagination={})

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        
        if not name or not email or not message:
            flash('All fields are required', 'error')
            return render_template('contact.html')
        
        # In a real application, you would send the message or store it
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('main.contact'))
    
    return render_template('contact.html')

@main_bp.route('/search')
def search():
    """Search trips and destinations"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return render_template('search.html', results=[], query='')
    
    if 'user_id' in session:
        # Search user's trips
        user_trips = trip_model.get_user_trips(session['user_id'])
        trip_results = [
            trip for trip in user_trips
            if query.lower() in trip.get('title', '').lower() or
               query.lower() in trip.get('destination', '').lower() or
               query.lower() in trip.get('start_location', '').lower()
        ]
    else:
        trip_results = []
    
    # You could also add destination search here
    destination_results = []
    
    results = {
        'trips': trip_results,
        'destinations': destination_results
    }
    
    return render_template('search.html', results=results, query=query)