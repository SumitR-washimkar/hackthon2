document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.section');
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabContents = document.querySelectorAll('.tab-content');

    // Sidebar navigation
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));
            link.classList.add('active');
            const sectionId = link.getAttribute('data-section');
            document.getElementById(sectionId).classList.add('active');
        });
    });

    // Tabs in expenses section
    tabLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            tabLinks.forEach(l => l.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            link.classList.add('active');
            const tabId = link.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
            
            // Load uploaded expenses when switching to uploaded tab
            if (tabId === 'uploaded') {
                loadUploadedExpenses();
            }
        });
    });

    // OCR Upload and Processing
    const uploadBtn = document.getElementById('upload-btn');
    const receiptUpload = document.getElementById('receipt-upload');
    const expenseForm = document.getElementById('expense-form');
    const loadingIndicator = document.getElementById('loading-indicator');

    uploadBtn.addEventListener('click', async () => {
        const file = receiptUpload.files[0];
        
        if (!file) {
            showNotification('Please select an image file.', 'error');
            return;
        }

        // Validate file type
        const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            showNotification('Please upload a valid image file (PNG, JPEG, GIF, BMP, WEBP)', 'error');
            return;
        }

        // Validate file size (max 10MB)
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            showNotification('File size must be less than 10MB', 'error');
            return;
        }

        // Show loading state
        uploadBtn.disabled = true;
        uploadBtn.textContent = 'Processing...';
        if (loadingIndicator) loadingIndicator.style.display = 'block';

        const formData = new FormData();
        formData.append('receipt', file);

        try {
            const response = await fetch('/api/ocr', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || 'OCR processing failed');
            }

            if (result.success && result.data) {
                // Populate form fields with extracted data
                populateFormFields(result.data);
                
                // Show form
                expenseForm.style.display = 'block';
                
                // Scroll to form
                expenseForm.scrollIntoView({ behavior: 'smooth', block: 'start' });
                
                showNotification('Receipt processed successfully! Please verify the details.', 'success');
            } else {
                throw new Error('No data extracted from receipt');
            }

        } catch (error) {
            console.error('OCR Error:', error);
            showNotification(`Error: ${error.message}`, 'error');
            
            // Show empty form for manual entry
            expenseForm.style.display = 'block';
        } finally {
            // Reset button state
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Upload & Extract';
            if (loadingIndicator) loadingIndicator.style.display = 'none';
        }
    });

    // Populate form fields with OCR extracted data
    function populateFormFields(data) {
        // Employee name (from OCR or use logged-in user's name)
        const employeeField = document.getElementById('employee');
        if (employeeField) {
            employeeField.value = data.employee || getUserName() || '';
        }

        // Description
        const descriptionField = document.getElementById('description');
        if (descriptionField) {
            descriptionField.value = data.description || '';
        }

        // Date
        const dateField = document.getElementById('date');
        if (dateField) {
            dateField.value = data.date || new Date().toISOString().split('T')[0];
        }

        // Category
        const categoryField = document.getElementById('category');
        if (categoryField && data.category) {
            categoryField.value = data.category;
        }

        // Paid by
        const paidByField = document.getElementById('paid_by');
        if (paidByField && data.paid_by) {
            paidByField.value = data.paid_by;
        }

        // Remark
        const remarkField = document.getElementById('remark');
        if (remarkField) {
            remarkField.value = data.remark || '';
        }

        // Amount
        const amountField = document.getElementById('amount');
        if (amountField) {
            amountField.value = data.amount || '';
        }
    }

    // Submit expense form
    if (expenseForm) {
        expenseForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Gather form data
            const expenseData = {
                employee: document.getElementById('employee').value,
                description: document.getElementById('description').value,
                date: document.getElementById('date').value,
                category: document.getElementById('category').value,
                paid_by: document.getElementById('paid_by').value,
                remark: document.getElementById('remark').value,
                amount: parseFloat(document.getElementById('amount').value),
                status: document.getElementById('status')?.value || 'Pending',
                submitted: new Date().toISOString(),
                user_id: getUserId(),
                company_id: localStorage.getItem('company_id')
            };

            // Validate required fields
            if (!expenseData.description || !expenseData.amount || !expenseData.date) {
                showNotification('Please fill in all required fields (Description, Amount, Date)', 'error');
                return;
            }

            try {
                const response = await fetch('/api/expenses', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${getToken()}`
                    },
                    body: JSON.stringify(expenseData)
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.detail || 'Failed to submit expense');
                }

                showNotification('Expense submitted successfully!', 'success');
                
                // Reset form
                expenseForm.reset();
                expenseForm.style.display = 'none';
                receiptUpload.value = '';

                // Switch to uploaded tab and refresh data
                const uploadedTab = document.querySelector('.tab-link[data-tab="uploaded"]');
                if (uploadedTab) {
                    uploadedTab.click();
                }

                // Refresh uploaded expenses list
                loadUploadedExpenses();

            } catch (error) {
                console.error('Submit Error:', error);
                showNotification(`Error: ${error.message}`, 'error');
            }
        });
    }

    // Load uploaded expenses
    async function loadUploadedExpenses() {
        const userId = getUserId();
        
        if (!userId) {
            console.error('No user ID found');
            showNotification('Please login to view expenses', 'error');
            return;
        }

        console.log('Loading expenses for user:', userId);

        try {
            const response = await fetch(`/api/expenses?user_id=${userId}`, {
                headers: {
                    'Authorization': `Bearer ${getToken()}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to fetch expenses');
            }

            const expenses = await response.json();
            console.log('Loaded expenses:', expenses);
            
            displayUploadedExpenses(expenses);

        } catch (error) {
            console.error('Error loading expenses:', error);
            showNotification('Failed to load expenses', 'error');
            displayUploadedExpenses([]);
        }
    }

    // Display uploaded expenses in table
    function displayUploadedExpenses(expenses) {
        const tableBody = document.getElementById('uploaded-expenses-tbody');
        if (!tableBody) {
            console.error('Table body element not found');
            return;
        }

        if (!expenses || expenses.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 20px;">No expenses uploaded yet</td></tr>';
            return;
        }

        tableBody.innerHTML = expenses.map(expense => `
            <tr>
                <td>${formatDate(expense.date)}</td>
                <td>${escapeHtml(expense.description || '-')}</td>
                <td>${escapeHtml(expense.category || 'Other')}</td>
                <td>${escapeHtml(expense.paid_by || 'Cash')}</td>
                <td>₹${parseFloat(expense.amount || 0).toFixed(2)}</td>
                <td><span class="status-badge status-${(expense.status || 'pending').toLowerCase()}">${expense.status || 'Pending'}</span></td>
                <td>${escapeHtml(expense.remark || '-')}</td>
                <td>
                    <button onclick="viewExpense('${expense.expense_id}')" class="btn-action">View</button>
                    ${expense.status === 'Pending' ? `<button onclick="deleteExpense('${expense.expense_id}')" class="btn-action btn-delete">Delete</button>` : ''}
                </td>
            </tr>
        `).join('');
    }

    // Make functions globally available
    window.viewExpense = function(expenseId) {
        console.log('Viewing expense:', expenseId);
        showNotification('View functionality coming soon', 'info');
        // TODO: Implement view expense modal
    };

    window.deleteExpense = async function(expenseId) {
        if (!confirm('Are you sure you want to delete this expense?')) {
            return;
        }

        try {
            const response = await fetch(`/api/expenses/${expenseId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${getToken()}`
                }
            });

            if (!response.ok) {
                throw new Error('Failed to delete expense');
            }

            showNotification('Expense deleted successfully', 'success');
            loadUploadedExpenses();

        } catch (error) {
            console.error('Delete error:', error);
            showNotification('Failed to delete expense', 'error');
        }
    };

    // Utility: Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Utility: Show notification
    function showNotification(message, type = 'info') {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(n => n.remove());

        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
            color: white;
            border-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 10000;
            max-width: 400px;
        `;

        document.body.appendChild(notification);

        // Auto remove after 4 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.3s';
            setTimeout(() => notification.remove(), 300);
        }, 4000);
    }

    // Utility: Format date
    function formatDate(dateString) {
        if (!dateString) return '-';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric' 
            });
        } catch (e) {
            return dateString;
        }
    }

    // Load expenses on page load
    loadUploadedExpenses();
});