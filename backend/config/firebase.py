import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', './firebase_key.json')
        cred = credentials.Certificate(cred_path)
        
        firebase_admin.initialize_app(cred, {
            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')  # Add this to .env
        })
        
        print("✅ Firebase initialized successfully")
        return True
    except ValueError:
        # Already initialized
        print("⚠️ Firebase already initialized")
        return True
    except Exception as e:
        print(f"❌ Firebase initialization error: {e}")
        return False

# Get Firestore client
def get_firestore_client():
    """Get Firestore database client"""
    return firestore.client()

# Get Firebase Auth
def get_auth():
    """Get Firebase Auth"""
    return auth

# Get Storage bucket
def get_storage_bucket():
    """Get Firebase Storage bucket"""
    try:
        return storage.bucket()
    except Exception as e:
        print(f"⚠️ Storage bucket not configured: {e}")
        return None

# Initialize on module import
initialize_firebase()

# Export instances
db = get_firestore_client()
firebase_auth = get_auth()
bucket = get_storage_bucket()