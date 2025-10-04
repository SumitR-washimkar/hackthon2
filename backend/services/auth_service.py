from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.config.firebase import firebase_auth
from backend.models.user import User
from typing import Optional

security = HTTPBearer()

def create_user_with_email_password(email: str, password: str) -> str:
    """
    Create a new user in Firebase Authentication
    Returns the user_id (uid) if successful, None otherwise
    """
    try:
        user = firebase_auth.create_user(
            email=email,
            password=password,
            email_verified=False
        )
        return user.uid
    except Exception as e:
        print(f"Error creating user: {e}")
        return None


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify Firebase ID token from Authorization header
    Returns decoded token data
    """
    try:
        token = credentials.credentials
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Error verifying token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


def get_current_user(token_data: dict = Depends(verify_token)) -> User:
    """
    Get current user from token data
    """
    try:
        user_id = token_data.get('uid')
        role = token_data.get('role')
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token data"
            )
        
        # Try to get user from Firestore
        user = User.get_user_by_id(user_id, role) if role else None
        
        if not user:
            # Try all roles if role not in token
            for r in User.VALID_ROLES:
                user = User.get_user_by_id(user_id, r)
                if user:
                    break
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user data"
        )


def require_role(*allowed_roles: str):
    """
    Dependency to check if user has required role
    Usage: require_role('admin', 'manager')
    """
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(allowed_roles)}"
            )
        return user
    return role_checker


def create_user_in_auth(email: str, password: str, name: str, role: str) -> Optional[str]:
    """
    Create user in Firebase Auth with custom claims
    """
    try:
        user_record = firebase_auth.create_user(
            email=email,
            password=password,
            display_name=name
        )
        
        # Set custom claims
        firebase_auth.set_custom_user_claims(user_record.uid, {'role': role})
        
        return user_record.uid
    except Exception as e:
        print(f"Error creating user in auth: {e}")
        return None


def create_admin_user(email: str, password: str, name: str) -> Optional[str]:
    """
    Create admin user with admin role
    """
    return create_user_in_auth(email, password, name, 'admin')


def get_user_by_email(email: str):
    """Get user from Firebase Auth by email"""
    try:
        user = firebase_auth.get_user_by_email(email)
        return user
    except Exception as e:
        print(f"Error getting user: {e}")
        return None


def delete_user(uid: str) -> bool:
    """Delete user from Firebase Authentication"""
    try:
        firebase_auth.delete_user(uid)
        return True
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False


def update_user_password(uid: str, new_password: str) -> bool:
    """Update user password in Firebase Authentication"""
    try:
        firebase_auth.update_user(uid, password=new_password)
        return True
    except Exception as e:
        print(f"Error updating password: {e}")
        return False