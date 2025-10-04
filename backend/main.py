from fastapi import FastAPI, HTTPException, status, Request, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import httpx
from datetime import datetime
import os
from dotenv import load_dotenv

# Import Firebase config
from backend.config.firebase import db, firebase_auth
from backend.models.user import User
from backend.services.auth_service import verify_token, get_current_user
from backend.services.ocr_service import ocr_service

load_dotenv()

app = FastAPI(title="Expense Management API", version="1.0.0")

# CORS Configuration
origins = os.getenv("CORS_ORIGINS", "http://localhost:5500").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup static files and templates
frontend_path = os.path.join(os.path.dirname(__file__), "..", "Frontend")
static_path = os.path.join(frontend_path, "static")
templates_path = os.path.join(frontend_path, "templates")

# Mount static files (CSS and JS)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=templates_path)

# Pydantic Models
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirm_password: str
    country: str
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class SignupResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[str] = None
    company_id: Optional[str] = None
    
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[dict] = None
    redirect_url: Optional[str] = None

class CreateEmployeeRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirmPassword: str
    role: str
    manager_id: Optional[str] = None
    company_id: str

# ========================================
# OCR ENDPOINT - DIRECTLY IN MAIN.PY
# ========================================

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}

def validate_image_file(file: UploadFile) -> None:
    """Validate uploaded image file"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")

@app.post("/api/ocr")
async def process_receipt_ocr(receipt: UploadFile = File(...)):
    """
    Process receipt image with OCR and extract expense details
    """
    try:
        print(f"📸 Receiving OCR request for file: {receipt.filename}")
        
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
        
        print(f"📄 File size: {len(file_content)} bytes")
        
        # Process with OCR
        extracted_data = ocr_service.extract_expense_details(file_content)
        
        print(f"✅ OCR completed. Extracted data: {extracted_data}")
        
        # Return extracted data
        return {
            "success": True,
            "message": "Receipt processed successfully",
            "data": extracted_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error processing receipt: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process receipt: {str(e)}"
        )

# ========================================
# EXPENSE ENDPOINTS
# ========================================

@app.get("/api/expenses")
async def get_user_expenses(user_id: str = None):
    """Get all expenses for current user"""
    try:
        from backend.models.expense import Expense
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        expenses = Expense.get_user_expenses(user_id)
        return expenses
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting expenses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/expenses")
async def create_expense(expense_data: dict):
    """Create new expense"""
    try:
        from backend.models.expense import Expense, ExpenseCreate
        
        print(f"Creating expense with data: {expense_data}")
        
        # Validate expense data
        validated_data = ExpenseCreate(**expense_data)
        
        # Add user_id and company_id
        expense_dict = validated_data.dict()
        expense_dict['user_id'] = expense_data.get('user_id')
        expense_dict['company_id'] = expense_data.get('company_id')
        
        # Create expense
        expense_id = Expense.create_expense(expense_dict)
        
        print(f"✅ Expense created successfully with ID: {expense_id}")
        
        return {
            "success": True,
            "message": "Expense created successfully",
            "expense_id": expense_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating expense: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/expenses/{expense_id}")
async def delete_expense(expense_id: str):
    """Delete an expense"""
    try:
        from backend.models.expense import Expense
        
        print(f"Deleting expense: {expense_id}")
        
        # Delete expense
        success = Expense.delete_expense(expense_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Expense not found")
        
        return {
            "success": True,
            "message": "Expense deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting expense: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========================================
# PAGE ROUTES
# ========================================

@app.get("/")
async def read_root(request: Request):
    """Serve index.html"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/signup")
async def read_signup(request: Request):
    """Serve signup.html"""
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/login")
async def read_login(request: Request):
    """Serve login.html"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/forgot-password")
async def read_forgot_password(request: Request):
    """Serve forgot_password.html"""
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.get("/employee_expenses")
async def read_employee_expenses(request: Request):
    """Serve employee expenses page"""
    return templates.TemplateResponse("employee_expenses.html", {"request": request})

@app.get("/admin_dashboard")
async def admin_dashboard(request: Request):
    """Serve admin dashboard"""
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

@app.get("/manager_dashboard")
async def manager_dashboard(request: Request):
    """Serve manager dashboard"""
    return templates.TemplateResponse("manager_dashboard.html", {"request": request})

@app.get("/employee_dashboard")
async def employee_dashboard(request: Request):
    """Serve employee dashboard"""
    return templates.TemplateResponse("employee_dashboard.html", {"request": request})

@app.get("/admin_create")
async def admin_create(request: Request):
    """Serve admin create employee page"""
    return templates.TemplateResponse("admin_create.html", {"request": request})

@app.get("/admin_expenses")
async def admin_expenses(request: Request):
    """Serve admin expenses management page"""
    return templates.TemplateResponse("admin_expenses.html", {"request": request})

# ========================================
# AUTH & USER MANAGEMENT
# ========================================

async def get_country_currency(country_name: str):
    """Fetch currency for selected country"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://restcountries.com/v3.1/all?fields=name,currencies"
            )
            countries = response.json()
            
            for country in countries:
                if country['name']['common'].lower() == country_name.lower():
                    currencies = country.get('currencies', {})
                    if currencies:
                        currency_code = list(currencies.keys())[0]
                        return currency_code
            
            return "USD"
    except Exception as e:
        print(f"Error fetching currency: {e}")
        return "USD"

@app.post("/api/signup", response_model=SignupResponse)
async def signup(signup_data: SignupRequest):
    """Create admin user account with company"""
    try:        
        if User.admin_exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin account already exists. Only one admin is allowed in the system."
            )
        
        currency = await get_country_currency(signup_data.country)
        
        try:
            user_record = firebase_auth.create_user(
                email=signup_data.email,
                password=signup_data.password,
                display_name=signup_data.name
            )
            user_id = user_record.uid
        except Exception as auth_error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Authentication error: {str(auth_error)}"
            )
        
        firebase_auth.set_custom_user_claims(user_id, {'role': 'admin'})
        
        company_ref = db.collection('companies').document()
        company_id = company_ref.id
        
        company_data = {
            'company_id': company_id,
            'name': f"{signup_data.name}'s Company",
            'country': signup_data.country,
            'currency': currency,
            'admin_id': user_id,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        company_ref.set(company_data)
        
        user_data = {
            'user_id': user_id,
            'email': signup_data.email,
            'name': signup_data.name,
            'role': 'admin',
            'company_id': company_id,
            'manager_id': None,
            'is_manager_approver': False
        }
        
        User.create_user_in_firestore(user_data)
        
        return SignupResponse(
            success=True,
            message="Admin account created successfully. You are the first and only admin.",
            user_id=user_id,
            company_id=company_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        try:
            if 'user_id' in locals():
                firebase_auth.delete_user(user_id)
            if 'company_id' in locals():
                db.collection('companies').document(company_id).delete()
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )
        
@app.post("/api/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Login user"""
    try:
        user = User.get_user_by_email(login_data.email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        redirect_map = {
            'admin': '/admin_dashboard',
            'manager': '/manager_dashboard',
            'employee': '/employee_dashboard'
        }
        
        redirect_url = redirect_map.get(user.role, '/employee_dashboard')
        
        return LoginResponse(
            success=True,
            message="Login successful",
            token=None,
            user={
                'user_id': user.user_id,
                'name': user.name,
                'email': user.email,
                'role': user.role,
                'company_id': user.company_id
            },
            redirect_url=redirect_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@app.post("/api/create-employee")
async def create_employee(employee_data: CreateEmployeeRequest):
    """Create new employee or manager"""
    try:
        if User.get_user_by_email(employee_data.email):
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        if employee_data.role not in ['employee', 'manager']:
            raise HTTPException(status_code=400, detail="Invalid role")
        
        user_record = firebase_auth.create_user(
            email=employee_data.email,
            password=employee_data.password,
            display_name=employee_data.name
        )
        
        print(f"Created user in Firebase Auth: {user_record.uid}")
        
        firebase_auth.set_custom_user_claims(user_record.uid, {'role': employee_data.role})
        
        user_data = {
            'user_id': user_record.uid,
            'email': employee_data.email,
            'name': employee_data.name,
            'role': employee_data.role,
            'company_id': employee_data.company_id,
            'manager_id': employee_data.manager_id,
            'is_manager_approver': employee_data.role == 'manager'
        }
        
        success = User.create_user_in_firestore(user_data)
        
        if not success:
            firebase_auth.delete_user(user_record.uid)
            raise HTTPException(status_code=500, detail="Failed to save user to database")
        
        print(f"Created user in Firestore: {employee_data.role}/details/{user_record.uid}")
        
        return {"success": True, "message": "Employee created successfully", "user_id": user_record.uid}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating employee: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/managers")
async def get_managers(company_id: str):
    """Get all managers in a company"""
    try:
        if not company_id:
            raise HTTPException(status_code=400, detail="company_id is required")
        
        managers = User.get_managers_by_company(company_id)
        
        return [
            {
                "user_id": m.user_id,
                "name": m.name,
                "email": m.email
            }
            for m in managers
        ]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching managers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch managers: {str(e)}")

# Test endpoint to verify server is running
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Server is running"}