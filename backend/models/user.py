from datetime import datetime
from typing import Optional, Dict, Any, List
from backend.config.firebase import db

class User:
    """User model for Firestore with role-based collections"""
    
    # Role constants
    ROLE_ADMIN = 'admin'
    ROLE_MANAGER = 'manager'
    ROLE_EMPLOYEE = 'employee'
    
    VALID_ROLES = [ROLE_ADMIN, ROLE_MANAGER, ROLE_EMPLOYEE]
    
    def __init__(self, user_id: str, email: str, name: str, role: str, 
                 company_id: str, manager_id: Optional[str] = None,
                 is_manager_approver: bool = False,
                 created_at: Optional[datetime] = None):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.role = role
        self.company_id = company_id
        self.manager_id = manager_id
        self.is_manager_approver = is_manager_approver
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user object to dictionary for Firestore"""
        return {
            'user_id': self.user_id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'company_id': self.company_id,
            'manager_id': self.manager_id,
            'is_manager_approver': self.is_manager_approver,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'User':
        """Create User object from Firestore dictionary"""
        return User(
            user_id=data.get('user_id'),
            email=data.get('email'),
            name=data.get('name'),
            role=data.get('role'),
            company_id=data.get('company_id'),
            manager_id=data.get('manager_id'),
            is_manager_approver=data.get('is_manager_approver', False),
            created_at=data.get('created_at')
        )
    
    @staticmethod
    def create_user_in_firestore(user_data: Dict[str, Any]) -> bool:
        """Create user document in role-based collection"""
        try:
            user = User(
                user_id=user_data['user_id'],
                email=user_data['email'],
                name=user_data['name'],
                role=user_data['role'],
                company_id=user_data['company_id'],
                manager_id=user_data.get('manager_id'),
                is_manager_approver=user_data.get('is_manager_approver', False)
            )
            
            # Save to role-based collection: users/{role}/{user_id}
            db.collection('users').document(user.role).collection('details').document(user.user_id).set(user.to_dict())
            return True
        except Exception as e:
            print(f"Error creating user in Firestore: {e}")
            return False
    
    @staticmethod
    def get_user_by_id(user_id: str, role: str) -> Optional['User']:
        """Get user by user_id and role from Firestore"""
        try:
            user_doc = db.collection('users').document(role).collection('details').document(user_id).get()
            if user_doc.exists:
                return User.from_dict(user_doc.to_dict())
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional['User']:
        """Get user by email from all role collections"""
        try:
            for role in User.VALID_ROLES:
                users = db.collection('users').document(role).collection('details').where('email', '==', email).limit(1).stream()
                for user_doc in users:
                    return User.from_dict(user_doc.to_dict())
            return None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    @staticmethod
    def admin_exists() -> bool:
        """Check if an admin user already exists"""
        try:
            admins = db.collection('users').document('admin').collection('details').limit(1).stream()
            return any(True for _ in admins)
        except Exception as e:
            print(f"Error checking admin existence: {e}")
            return False
    
    @staticmethod
    def get_users_by_role(role: str, company_id: Optional[str] = None) -> List['User']:
        """Get all users by role, optionally filtered by company"""
        try:
            users = []
            query = db.collection('users').document(role).collection('details')
            
            if company_id:
                query = query.where('company_id', '==', company_id)
            
            user_docs = query.stream()
            for doc in user_docs:
                users.append(User.from_dict(doc.to_dict()))
            return users
        except Exception as e:
            print(f"Error getting users by role: {e}")
            return []
    
    @staticmethod
    def get_managers_by_company(company_id: str) -> List['User']:
        """Get all managers in a company"""
        return User.get_users_by_role(User.ROLE_MANAGER, company_id)
    
@staticmethod
def get_user_by_email_all_roles(user_id: str) -> Optional['User']:
    """Get user by ID from any role collection"""
    try:
        for role in User.VALID_ROLES:
            user = User.get_user_by_id(user_id, role)
            if user:
                return user
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None 