from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from typing import List
import os

from backend.services.ocr_service import ocr_service
from backend.services.auth_service import verify_token
from backend.models.expense import Expense
from backend.models.expense import Expense, ExpenseCreate


router = APIRouter(prefix="/api", tags=["user"])

# Maximum file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed image formats
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}

def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file"""
    # Check file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check content type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")


@router.post("/ocr")
async def process_receipt_ocr(
    receipt: UploadFile = File(...),
    # Uncomment when authentication is ready:
    # token_data: dict = Depends(verify_token)
):
    """
    Process receipt image with OCR and extract expense details
    
    Returns:
        - employee: Employee name (if found)
        - description: Merchant/business name
        - date: Transaction date (YYYY-MM-DD format)
        - category: Expense category
        - paid_by: Payment method
        - remark: Additional notes
        - amount: Total amount
    """
    try:
        # Validate file
        validate_image_file(receipt)
        
        # Read file content
        file_content = await receipt.read()
        
        # Check file size
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        # Process with OCR
        extracted_data = ocr_service.extract_expense_details(file_content)
        
        # Return extracted data
        return {
            "success": True,
            "message": "Receipt processed successfully",
            "data": extracted_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing receipt: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process receipt: {str(e)}"
        )


@router.get("/expenses")
async def get_user_expenses(
    user_id: str = None,
    # token_data: dict = Depends(verify_token)
):
    """Get all expenses for current user"""
    try:
        
        # If no user_id provided, get from token (when auth is enabled)
        # For now, require user_id as query parameter
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        expenses = Expense.get_user_expenses(user_id)
        return expenses
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting expenses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/expenses")
async def create_expense(
    expense_data: dict,
    # token_data: dict = Depends(verify_token)
):
    """Create new expense"""
    try:
        
        # Validate expense data
        validated_data = ExpenseCreate(**expense_data)
        
        # Add user_id and company_id
        expense_dict = validated_data.dict()
        expense_dict['user_id'] = expense_data.get('user_id')
        expense_dict['company_id'] = expense_data.get('company_id')
        
        # Create expense
        expense_id = Expense.create_expense(expense_dict)
        
        return {
            "success": True,
            "message": "Expense created successfully",
            "expense_id": expense_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating expense: {e}")
        raise HTTPException(status_code=500, detail=str(e))