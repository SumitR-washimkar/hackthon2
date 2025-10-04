// API Helper Functions
const API_BASE_URL = window.location.origin;

// Get stored token
function getToken() {
    return localStorage.getItem('access_token');
}

// Get user role
function getUserRole() {
    return localStorage.getItem('user_role');
}

// Get user ID
function getUserId() {
    return localStorage.getItem('user_id');
}

// Get user name
function getUserName() {
    return localStorage.getItem('user_name');
}

// Get company ID
function getCompanyId() {
    return localStorage.getItem('company_id');
}

// Check if user is logged in
function isLoggedIn() {
    return !!getToken();
}

// Logout user
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_role');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_name');
    localStorage.removeItem('company_id');
    window.location.href = '/login';
}

// Make authenticated API request
async function apiRequest(endpoint, options = {}) {
    const token = getToken();
    
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const config = {
        ...options,
        headers
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        
        // If unauthorized, redirect to login
        if (response.status === 401) {
            logout();
            return;
        }
        
        const data = await response.json();
        
        return {
            ok: response.ok,
            status: response.status,
            data
        };
    } catch (error) {
        console.error('API Request Error:', error);
        throw error;
    }
}

// API Methods
const API = {
    // Auth endpoints
    login: (email, password) => 
        apiRequest('/api/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        }),
    
    signup: (userData) => 
        apiRequest('/api/signup', {
            method: 'POST',
            body: JSON.stringify(userData)
        }),
    
    forgotPassword: (email) => 
        apiRequest('/api/forgot-password', {
            method: 'POST',
            body: JSON.stringify({ email })
        }),
    
    // User endpoints
    getCurrentUser: () => apiRequest('/api/users/me'),
    
    // Admin endpoints
    createEmployee: (employeeData) => 
        apiRequest('/api/create-employee', {
            method: 'POST',
            body: JSON.stringify(employeeData)
        }),
    
    getManagers: (companyId) => 
        apiRequest(`/api/managers?company_id=${companyId}`),
    
    // Expense endpoints
    getExpenses: () => apiRequest('/api/expenses'),
    
    createExpense: (expenseData) => 
        apiRequest('/api/expenses', {
            method: 'POST',
            body: JSON.stringify(expenseData)
        }),
    
    // OCR endpoint - NEW
    uploadReceiptForOCR: async (file) => {
        const token = getToken();
        const formData = new FormData();
        formData.append('receipt', file);
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/ocr`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });
            
            if (response.status === 401) {
                logout();
                return;
            }
            
            const data = await response.json();
            
            return {
                ok: response.ok,
                status: response.status,
                data
            };
        } catch (error) {
            console.error('OCR Upload Error:', error);
            throw error;
        }
    }
};

// Redirect to appropriate dashboard based on role
function redirectToDashboard() {
    const role = getUserRole();
    
    if (!isLoggedIn()) {
        window.location.href = '/login';
        return;
    }
    
    switch(role) {
        case 'admin':
            window.location.href = '/admin_dashboard';
            break;
        case 'manager':
            window.location.href = '/manager_dashboard';
            break;
        case 'employee':
            window.location.href = '/employee_dashboard';
            break;
        default:
            logout();
    }
}

// Check authentication on protected pages
function requireAuth(allowedRoles = []) {
    if (!isLoggedIn()) {
        window.location.href = '/login';
        return false;
    }
    
    const userRole = getUserRole();
    
    if (allowedRoles.length > 0 && !allowedRoles.includes(userRole)) {
        alert('You do not have permission to access this page');
        redirectToDashboard();
        return false;
    }
    
    return true;
}