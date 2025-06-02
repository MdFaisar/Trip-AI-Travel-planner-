# TripAI Flask Application - Complete Setup Guide

## Project Structure
```
tripai-flask/
├── app.py                          # Main Flask application
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── firebase_config.py              # Firebase configuration
├── models.py                       # Database models
├── auth.py                         # Authentication routes
├── main.py                         # Main application routes
├── pdf_generator.py                # PDF generation utility
├── prompt.py                       # AI prompt generation
├── utils.py                        # Utility functions
├── .env                           # Environment variables
├── .gitignore                     # Git ignore file
├── static/                        # Static files
│   ├── css/
│   │   ├── style.css             # Main stylesheet
│   │   ├── auth.css              # Authentication pages styling
│   │   └── dashboard.css         # Dashboard styling
│   ├── js/
│   │   ├── main.js               # Main JavaScript
│   │   └── auth.js               # Authentication JavaScript
│   └── images/                   # Image assets
├── templates/                     # HTML templates
│   ├── base.html                 # Base template
│   ├── index.html                # Home page
│   ├── login.html                # Login page
│   ├── register.html             # Registration page
│   ├── dashboard.html            # User dashboard
│   ├── trip_planner.html         # Trip planning form
│   ├── trip_result.html          # Trip plan results
│   └── profile.html              # User profile
└── assets/                       # Font and other assets
    └── Arial Unicode.ttf         # Font for PDF generation
```

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- Firebase account
- Groq API key

### 2. Clone and Setup Virtual Environment
```bash
# Create project directory
mkdir tripai-flask
cd tripai-flask

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
Create requirements.txt and install packages:
```bash
pip install -r requirements.txt
```

### 4. Firebase Setup
1. Go to https://console.firebase.google.com/
2. Create a new project named "TripAI"
3. Enable Authentication with Email/Password
4. Create Firestore Database in production mode
5. Generate service account key:
   - Go to Project Settings > Service Accounts
   - Generate new private key
   - Save as `firebase-service-account-key.json` in project root

### 5. Environment Variables
Create `.env` file in project root:
```
GROQ_API_KEY=your_groq_api_key_here
FLASK_SECRET_KEY=your_secret_key_here
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_WEB_API_KEY=your_firebase_web_api_key
```

### 6. Run the Application
```bash
python app.py
```

The application will be available at http://localhost:5000

## Firebase Database Structure

### Collections:
1. **users** - User profiles
   ```json
   {
     "uid": "user_unique_id",
     "email": "user@example.com",
     "name": "User Name",
     "created_at": "timestamp",
     "profile_picture": "url_to_image"
   }
   ```

2. **trips** - Trip plans
   ```json
   {
     "trip_id": "unique_trip_id",
     "user_id": "user_uid",
     "title": "Trip Title",
     "start_location": "Starting Point",
     "destination": "Destination",
     "start_date": "2024-01-01",
     "end_date": "2024-01-05",
     "duration": 5,
     "budget": {
       "amount": 50000,
       "currency": "INR"
     },
     "trip_plan": "Generated trip plan content",
     "created_at": "timestamp",
     "status": "completed"
   }
   ```

## Key Features:
- User authentication (register/login/logout)
- Trip planning with AI integration
- Trip history and management
- PDF generation and download
- Responsive design
- Firebase integration for data persistence

## Security Considerations:
- Environment variables for sensitive data
- Firebase security rules
- CSRF protection
- Input validation and sanitization