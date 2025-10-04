from flask import Blueprint, request, jsonify
from backend.models.user import User
from backend.services.auth_service import create_user_with_email_password
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/api')

# Authentication decorator (simplified - adjust based on your auth implementation)
def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Add your token validation logic here
        # For now, this is a placeholder
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/managers', methods=['GET'])
def get_managers():
    """Get all managers for a specific company"""
    try:
        company_id = request.args.get('company_id')
        
        if not company_id:
            return jsonify({'error': 'company_id is required'}), 400
        
        # Fetch all managers from the company
        managers = User.get_managers_by_company(company_id)
        
        # Convert to list of dictionaries
        manager_list = [
            {
                'user_id': manager.user_id,
                'name': manager.name,
                'email': manager.email
            }
            for manager in managers
        ]
        
        return jsonify(manager_list), 200
        
    except Exception as e:
        print(f"Error fetching managers: {e}")
        return jsonify({'error': 'Failed to fetch managers'}), 500


@admin_bp.route('/create-employee', methods=['POST'])
def create_employee():
    """Create a new employee or manager"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'role', 'password', 'company_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'detail': f'{field} is required'}), 400
        
        # Validate role
        if data['role'] not in User.VALID_ROLES:
            return jsonify({'detail': 'Invalid role'}), 400
        
        # Check if user already exists
        existing_user = User.get_user_by_email(data['email'])
        if existing_user:
            return jsonify({'detail': 'User with this email already exists'}), 400
        
        # Validate password confirmation
        if data['password'] != data.get('confirmPassword'):
            return jsonify({'detail': 'Passwords do not match'}), 400
        
        # Create user in Firebase Authentication
        user_id = create_user_with_email_password(data['email'], data['password'])
        
        if not user_id:
            return jsonify({'detail': 'Failed to create user account'}), 500
        
        # Prepare user data for Firestore
        user_data = {
            'user_id': user_id,
            'email': data['email'],
            'name': data['name'],
            'role': data['role'],
            'company_id': data['company_id'],
            'manager_id': data.get('manager_id'),
            'is_manager_approver': False
        }
        
        # Create user in Firestore
        success = User.create_user_in_firestore(user_data)
        
        if success:
            return jsonify({
                'message': 'Employee created successfully',
                'user_id': user_id
            }), 201
        else:
            return jsonify({'detail': 'Failed to create user in database'}), 500
            
    except Exception as e:
        print(f"Error creating employee: {e}")
        return jsonify({'detail': f'An error occurred: {str(e)}'}), 500


@admin_bp.route('/employees', methods=['GET'])
def get_employees():
    """Get all employees for a company"""
    try:
        company_id = request.args.get('company_id')
        
        if not company_id:
            return jsonify({'error': 'company_id is required'}), 400
        
        employees = User.get_users_by_role(User.ROLE_EMPLOYEE, company_id)
        
        employee_list = [
            {
                'user_id': emp.user_id,
                'name': emp.name,
                'email': emp.email,
                'manager_id': emp.manager_id,
                'created_at': emp.created_at.isoformat() if emp.created_at else None
            }
            for emp in employees
        ]
        
        return jsonify(employee_list), 200
        
    except Exception as e:
        print(f"Error fetching employees: {e}")
        return jsonify({'error': 'Failed to fetch employees'}), 500