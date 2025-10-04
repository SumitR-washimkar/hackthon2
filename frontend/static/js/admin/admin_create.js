const API_URL = window.location.origin;

// Get current user
const user = JSON.parse(localStorage.getItem('user') || '{}');
const token = localStorage.getItem('token') || localStorage.getItem('access_token');

// Check authentication
if (!token || !user.company_id) {
    console.error('User not authenticated or missing company_id');
    alert('Please login again');
    window.location.href = '/login';
}

// Load managers for dropdown
async function loadManagers() {
    try {
        console.log('Loading managers for company:', user.company_id);
        
        const response = await fetch(`${API_URL}/api/managers?company_id=${user.company_id}`, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const managers = await response.json();
            console.log('Managers loaded:', managers);
            
            const managerSelect = document.getElementById('manager');
            
            // Clear existing options except the first one
            managerSelect.innerHTML = '<option value="">Select manager (optional)</option>';
            
            if (managers.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No managers available';
                option.disabled = true;
                managerSelect.appendChild(option);
            } else {
                managers.forEach(manager => {
                    const option = document.createElement('option');
                    option.value = manager.user_id;
                    option.textContent = `${manager.name} (${manager.email})`;
                    managerSelect.appendChild(option);
                });
            }
        } else {
            console.error('Failed to load managers:', response.status);
            showAlert('Failed to load managers. Please refresh the page.', 'error');
        }
    } catch (error) {
        console.error('Error loading managers:', error);
        showAlert('Error loading managers. Please check your connection.', 'error');
    }
}

// Show/hide manager selection based on role
document.getElementById('role').addEventListener('change', (e) => {
    const managerGroup = document.getElementById('managerGroup');
    if (e.target.value === 'employee') {
        managerGroup.style.display = 'block';
        // Reload managers when showing the dropdown
        loadManagers();
    } else {
        managerGroup.style.display = 'none';
    }
});

// Show alert
function showAlert(message, type) {
    const alert = document.getElementById('alert');
    alert.textContent = message;
    alert.className = `alert alert-${type} show`;
    
    setTimeout(() => {
        alert.className = 'alert';
    }, 5000);
}

// Show error
function showError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const error = document.getElementById(fieldId + 'Error');
    
    field.classList.add('error');
    error.textContent = message;
    error.classList.add('show');
}

// Clear error
function clearError(fieldId) {
    const field = document.getElementById(fieldId);
    const error = document.getElementById(fieldId + 'Error');
    
    field.classList.remove('error');
    error.classList.remove('show');
}

// Clear all errors
function clearAllErrors() {
    ['name', 'email', 'role', 'password', 'confirmPassword'].forEach(clearError);
}

// Validate form
function validateForm(formData) {
    clearAllErrors();
    let isValid = true;

    if (!formData.name.trim()) {
        showError('name', 'Please enter full name');
        isValid = false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
        showError('email', 'Please enter a valid email');
        isValid = false;
    }

    if (!formData.role) {
        showError('role', 'Please select a role');
        isValid = false;
    }

    if (formData.password.length < 6) {
        showError('password', 'Password must be at least 6 characters');
        isValid = false;
    }

    if (formData.password !== formData.confirmPassword) {
        showError('confirmPassword', 'Passwords do not match');
        isValid = false;
    }

    return isValid;
}

// Handle form submission
document.getElementById('createEmployeeForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        role: document.getElementById('role').value,
        password: document.getElementById('password').value,
        confirmPassword: document.getElementById('confirmPassword').value,
        manager_id: document.getElementById('manager').value || null,
        company_id: user.company_id
    };

    if (!validateForm(formData)) {
        return;
    }

    const submitBtn = document.getElementById('submitBtn');
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;

    try {
        console.log('Sending employee data:', formData);
        
        const response = await fetch(`${API_URL}/api/create-employee`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();
        console.log('Response:', data);

        if (response.ok) {
            showAlert('Employee created successfully!', 'success');
            document.getElementById('createEmployeeForm').reset();
            clearAllErrors();
            document.getElementById('managerGroup').style.display = 'none';
        } else {
            showAlert(data.detail || 'Failed to create employee', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('An error occurred. Please try again.', 'error');
    } finally {
        submitBtn.classList.remove('loading');
        submitBtn.disabled = false;
    }
});

// Reset button
document.getElementById('resetBtn').addEventListener('click', () => {
    document.getElementById('createEmployeeForm').reset();
    clearAllErrors();
    document.getElementById('managerGroup').style.display = 'none';
});

// Initialize - Load managers on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Page loaded, checking role selection...');
    // If employee role is already selected (unlikely on page load), load managers
    const roleSelect = document.getElementById('role');
    if (roleSelect.value === 'employee') {
        loadManagers();
    }
});