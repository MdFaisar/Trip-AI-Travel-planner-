import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth
import os
from config import Config
import datetime

class FirebaseConfig:
    """Enhanced Firebase configuration and initialization"""
    
    def __init__(self):
        self.db = None
        self.app = None
        self._initialize_firebase()

        # Test Firebase connection
        try:
            test_doc = self.db.collection('test').document('connection_test')
            test_doc.set({
                'timestamp': datetime.datetime.now(),
                'status': 'connected'
            })
            print("✅ Firebase connection successful")
            
            # Clean up test document
            test_doc.delete()
            
        except Exception as e:
            print(f"❌ Firebase connection failed: {e}")
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK with enhanced error handling"""
        try:
            if not firebase_admin._apps:
                # Load service account key
                service_account_path = 'firebase-service-account-key.json'
                
                if os.path.exists(service_account_path):
                    print("🔑 Using service account key file")
                    cred = credentials.Certificate(service_account_path)
                    self.app = firebase_admin.initialize_app(cred)
                else:
                    print("🌐 Using environment variables for Firebase credentials")
                    # For production, use environment variables
                    private_key = os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n')
                    
                    if not private_key:
                        raise ValueError("FIREBASE_PRIVATE_KEY environment variable is not set")
                    
                    cred = credentials.Certificate({
                        "type": "service_account",
                        "project_id": os.getenv('FIREBASE_PROJECT_ID'),
                        "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
                        "private_key": private_key,
                        "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
                        "client_id": os.getenv('FIREBASE_CLIENT_ID'),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL')
                    })
                    self.app = firebase_admin.initialize_app(cred)
                
                # Initialize Firestore
                self.db = firestore.client()
                print("🚀 Firebase Admin SDK initialized successfully!")
                
            else:
                self.db = firestore.client()
                print("♻️ Using existing Firebase app instance")
                
        except Exception as e:
            print(f"💥 Error initializing Firebase: {e}")
            raise e
    
    def get_db(self):
        """Get Firestore database instance"""
        return self.db
    
    def create_user(self, email, password, display_name=None):
        """Create a new user in Firebase Auth with enhanced error handling"""
        try:
            print(f"Creating Firebase Auth user: {email}")
            user = firebase_auth.create_user(
                email=email,
                password=password,
                display_name=display_name,
                email_verified=False  # User will need to verify email
            )
            print(f"✅ User created with UID: {user.uid}")
            return user
        except firebase_auth.EmailAlreadyExistsError:
            raise Exception("An account with this email already exists")
        except firebase_auth.WeakPasswordError:
            raise Exception("Password is too weak. Please choose a stronger password.")
        except firebase_auth.InvalidEmailError:
            raise Exception("Please enter a valid email address")
        except Exception as e:
            print(f"❌ Error creating user: {e}")
            raise Exception(f"Failed to create account: {str(e)}")
    
    def get_user_by_email(self, email):
        """Get user by email with error handling"""
        try:
            user = firebase_auth.get_user_by_email(email)
            return user
        except firebase_auth.UserNotFoundError:
            return None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    def get_user_by_uid(self, uid):
        """Get user by UID with error handling"""
        try:
            user = firebase_auth.get_user(uid)
            return user
        except firebase_auth.UserNotFoundError:
            return None
        except Exception as e:
            print(f"Error getting user by UID: {e}")
            return None
    
    def update_user_password(self, uid, new_password):
        """Update user password in Firebase Auth"""
        try:
            firebase_auth.update_user(
                uid,
                password=new_password
            )
            print(f"✅ Password updated for user: {uid}")
            return True
        except firebase_auth.UserNotFoundError:
            raise Exception("User not found")
        except firebase_auth.WeakPasswordError:
            raise Exception("Password is too weak")
        except Exception as e:
            print(f"❌ Error updating password: {e}")
            raise Exception(f"Failed to update password: {str(e)}")
    
    def update_user_profile(self, uid, **kwargs):
        """Update user profile in Firebase Auth"""
        try:
            firebase_auth.update_user(uid, **kwargs)
            print(f"✅ Profile updated for user: {uid}")
            return True
        except firebase_auth.UserNotFoundError:
            raise Exception("User not found")
        except Exception as e:
            print(f"❌ Error updating profile: {e}")
            raise Exception(f"Failed to update profile: {str(e)}")
    
    def verify_id_token(self, id_token):
        """Verify Firebase ID token with enhanced validation"""
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            return decoded_token
        except firebase_auth.ExpiredIdTokenError:
            print("ID token has expired")
            return None
        except firebase_auth.RevokedIdTokenError:
            print("ID token has been revoked")
            return None
        except firebase_auth.InvalidIdTokenError:
            print("Invalid ID token")
            return None
        except Exception as e:
            print(f"Error verifying ID token: {e}")
            return None
    
    def delete_user(self, uid):
        """Delete user from Firebase Auth with enhanced error handling"""
        try:
            firebase_auth.delete_user(uid)
            print(f"✅ User deleted: {uid}")
            return True
        except firebase_auth.UserNotFoundError:
            print(f"User not found for deletion: {uid}")
            return True  # Consider this a success since user doesn't exist
        except Exception as e:
            print(f"❌ Error deleting user: {e}")
            return False
    
    def send_password_reset_email(self, email):
        """Send password reset email (using Admin SDK)"""
        try:
            link = firebase_auth.generate_password_reset_link(email)
            # You would typically send this link via your email service
            print(f"Password reset link generated for {email}")
            return True
        except firebase_auth.UserNotFoundError:
            # Don't reveal if user exists for security
            return True
        except Exception as e:
            print(f"Error generating password reset link: {e}")
            return False
    
    def send_email_verification(self, uid):
        """Send email verification to user"""
        try:
            link = firebase_auth.generate_email_verification_link(
                email=firebase_auth.get_user(uid).email
            )
            # You would typically send this link via your email service
            print(f"Email verification link generated for user: {uid}")
            return True
        except Exception as e:
            print(f"Error generating email verification link: {e}")
            return False
    
    def disable_user(self, uid):
        """Disable a user account"""
        try:
            firebase_auth.update_user(uid, disabled=True)
            print(f"✅ User disabled: {uid}")
            return True
        except Exception as e:
            print(f"❌ Error disabling user: {e}")
            return False
    
    def enable_user(self, uid):
        """Enable a user account"""
        try:
            firebase_auth.update_user(uid, disabled=False)
            print(f"✅ User enabled: {uid}")
            return True
        except Exception as e:
            print(f"❌ Error enabling user: {e}")
            return False
    
    def get_users(self, max_results=1000):
        """Get list of users (for admin purposes)"""
        try:
            users = []
            page = firebase_auth.list_users(max_results=max_results)
            for user in page.users:
                users.append({
                    'uid': user.uid,
                    'email': user.email,
                    'display_name': user.display_name,
                    'disabled': user.disabled,
                    'email_verified': user.email_verified,
                    'creation_timestamp': user.user_metadata.creation_timestamp
                })
            return users
        except Exception as e:
            print(f"Error getting users: {e}")
            return []
    
    def revoke_refresh_tokens(self, uid):
        """Revoke all refresh tokens for a user (force logout)"""
        try:
            firebase_auth.revoke_refresh_tokens(uid)
            print(f"✅ Refresh tokens revoked for user: {uid}")
            return True
        except Exception as e:
            print(f"❌ Error revoking tokens: {e}")
            return False

# Global Firebase instance
firebase_config = FirebaseConfig()

# Convenience functions for backward compatibility
def get_firebase_db():
    """Get Firestore database instance"""
    return firebase_config.get_db()

def create_firebase_user(email, password, display_name=None):
    """Create Firebase user"""
    return firebase_config._create_user(email, password, display_name)

def verify_firebase_token(token):
    """Verify Firebase ID token"""
    return firebase_config.verify_id_token(token)