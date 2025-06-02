# TripAI Flask Application

An AI-powered trip planning application built with Flask, Firebase, and Groq AI. Plan your perfect trip with intelligent recommendations, budget management, and personalized itineraries.

Live demonstration:

## ✨ Features

- 🤖 **AI-Powered Trip Planning** - Generate personalized itineraries using Groq AI
- 🔐 **User Authentication** - Secure registration and login with Firebase Auth
- 💰 **Budget Management** - Plan trips within your specified budget
- 📱 **Responsive Design** - Works seamlessly on desktop and mobile devices
- 📄 **PDF Generation** - Download your trip plans as PDF documents
- 📊 **Trip History** - View and manage all your planned trips
- 🔒 **Secure Data Storage** - All data stored securely in Firebase Firestore

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Firebase account
- Groq API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/tripai-flask.git
   cd tripai-flask
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Firebase Setup**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create a new project named "TripAI"
   - Enable Authentication with Email/Password
   - Create Firestore Database in production mode
   - Generate service account key:
     - Go to Project Settings > Service Accounts
     - Generate new private key
     - Save as `firebase-service-account-key.json` in project root

5. **Environment Variables**
   Create `.env` file in project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   FLASK_SECRET_KEY=your_secret_key_here
   FIREBASE_PROJECT_ID=your_firebase_project_id
   FIREBASE_WEB_API_KEY=your_firebase_web_api_key
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

The application will be available at `http://localhost:5000`

## 📁 Project Structure

```
tripai-flask/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── firebase_config.py          # Firebase configuration
├── models.py                   # Database models
├── auth.py                     # Authentication routes
├── main.py                     # Main application routes
├── pdf_generator.py            # PDF generation utility
├── prompt.py                   # AI prompt generation
├── utils.py                    # Utility functions
├── .env                        # Environment variables
├── .gitignore                  # Git ignore file
├── static/                     # Static files
│   ├── css/
│   │   ├── style.css          # Main stylesheet
│   │   ├── auth.css           # Authentication pages styling
│   │   └── dashboard.css      # Dashboard styling
│   ├── js/
│   │   ├── main.js            # Main JavaScript
│   │   └── auth.js            # Authentication JavaScript
│   └── images/                # Image assets
├── templates/                  # HTML templates
│   ├── base.html              # Base template
│   ├── index.html             # Home page
│   ├── login.html             # Login page
│   ├── register.html          # Registration page
│   ├── dashboard.html         # User dashboard
│   ├── trip_planner.html      # Trip planning form
│   ├── trip_result.html       # Trip plan results
│   └── profile.html           # User profile
└── assets/                    # Font and other assets
    └── Arial Unicode.ttf      # Font for PDF generation
```

## 🗄️ Database Structure

### Firebase Collections

#### Users Collection
```json
{
  "uid": "user_unique_id",
  "email": "user@example.com",
  "name": "User Name",
  "created_at": "timestamp",
  "profile_picture": "url_to_image"
}
```

#### Trips Collection
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

## 🔧 Configuration

### Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Your Groq API key for AI functionality | Yes |
| `FLASK_SECRET_KEY` | Secret key for Flask sessions | Yes |
| `FIREBASE_PROJECT_ID` | Your Firebase project ID | Yes |
| `FIREBASE_WEB_API_KEY` | Your Firebase web API key | Yes |

### Firebase Security Rules

Ensure your Firestore security rules are properly configured:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    match /trips/{tripId} {
      allow read, write: if request.auth != null && request.auth.uid == resource.data.user_id;
    }
  }
}
```

## 🛡️ Security Features

- Environment variables for sensitive data
- Firebase security rules
- CSRF protection
- Input validation and sanitization
- Secure session management

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/tripai-flask/issues) page
2. Create a new issue if your problem isn't already listed
3. Provide detailed information about your setup and the issue

## 🙏 Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - The web framework used
- [Firebase](https://firebase.google.com/) - Backend services
- [Groq](https://groq.com/) - AI API for trip planning
- [Bootstrap](https://getbootstrap.com/) - Frontend framework

---

**Made with ❤️ for travelers by travelers**
