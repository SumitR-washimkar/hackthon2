from datetime import datetime
from typing import Optional
from pydantic import BaseModel, validator
from backend.config.firebase import db

class Expense(BaseModel):
    """Expense model for managing employee expenses"""
    expense_id: Optional[str] = None
    user_id: str
    company_id: str
    employee: str  # Employee name
    description: str
    date: str  # Date of expense (YYYY-MM-DD)
    category: str  # Food, Transportation, Accommodation, etc.
    paid_by: str  # Cash, Credit Card, Debit Card, UPI
    remark: Optional[str] = None
    amount: float
    status: str = "Pending"  # Pending, Approved, Rejected
    submitted: Optional[str] = None  # Submission timestamp
    receipt_url: Optional[str] = None  # URL to uploaded receipt image
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v
    
    @validator('category')
    def valid_category(cls, v):
        valid_categories = [
            'Food', 'Transportation', 'Accommodation', 
            'Office Supplies', 'Entertainment', 'Medical', 
            'Utilities', 'Other'
        ]
        if v not in valid_categories:
            return 'Other'
        return v
    
    @validator('paid_by')
    def valid_payment_method(cls, v):
        valid_methods = ['Cash', 'Credit Card', 'Debit Card', 'UPI']
        if v not in valid_methods:
            return 'Cash'
        return v
    
    @validator('status')
    def valid_status(cls, v):
        valid_statuses = ['Pending', 'Approved', 'Rejected']
        if v not in valid_statuses:
            return 'Pending'
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @staticmethod
    def create_expense(expense_data: dict) -> str:
        """Create new expense in Firestore"""
        try:
            # Add timestamps
            expense_data['created_at'] = datetime.utcnow()
            expense_data['updated_at'] = datetime.utcnow()
            expense_data['submitted'] = datetime.utcnow().isoformat()
            
            # Create document reference
            expense_ref = db.collection('expenses').document()
            expense_data['expense_id'] = expense_ref.id
            
            # Save to Firestore
            expense_ref.set(expense_data)
            
            return expense_ref.id
        except Exception as e:
            print(f"Error creating expense: {e}")
            raise
    
    @staticmethod
    def get_expense_by_id(expense_id: str) -> Optional['Expense']:
        """Get expense by ID"""
        try:
            doc = db.collection('expenses').document(expense_id).get()
            if doc.exists:
                data = doc.to_dict()
                return Expense(**data)
            return None
        except Exception as e:
            print(f"Error getting expense: {e}")
            return None
    
    @staticmethod
    def get_user_expenses(user_id: str) -> list:
        """Get all expenses for a user"""
        try:
            expenses_ref = db.collection('expenses')
            query = expenses_ref.where('user_id', '==', user_id).order_by('created_at', direction='DESCENDING')
            
            expenses = []
            for doc in query.stream():
                expense_data = doc.to_dict()
                expenses.append(expense_data)
            
            return expenses
        except Exception as e:
            print(f"Error getting user expenses: {e}")
            return []
    
    @staticmethod
    def get_company_expenses(company_id: str) -> list:
        """Get all expenses for a company"""
        try:
            expenses_ref = db.collection('expenses')
            query = expenses_ref.where('company_id', '==', company_id).order_by('created_at', direction='DESCENDING')
            
            expenses = []
            for doc in query.stream():
                expense_data = doc.to_dict()
                expenses.append(expense_data)
            
            return expenses
        except Exception as e:
            print(f"Error getting company expenses: {e}")
            return []
    
    @staticmethod
    def update_expense_status(expense_id: str, status: str) -> bool:
        """Update expense status (Approved/Rejected)"""
        try:
            if status not in ['Approved', 'Rejected', 'Pending']:
                raise ValueError("Invalid status")
            
            expense_ref = db.collection('expenses').document(expense_id)
            expense_ref.update({
                'status': status,
                'updated_at': datetime.utcnow()
            })
            return True
        except Exception as e:
            print(f"Error updating expense status: {e}")
            return False
    
    @staticmethod
    def delete_expense(expense_id: str) -> bool:
        """Delete expense"""
        try:
            db.collection('expenses').document(expense_id).delete()
            return True
        except Exception as e:
            print(f"Error deleting expense: {e}")
            return False


class ExpenseCreate(BaseModel):
    """Schema for creating new expense"""
    employee: str
    description: str
    date: str
    category: str
    paid_by: str
    remark: Optional[str] = None
    amount: float
    status: str = "Pending"
    receipt_url: Optional[str] = None