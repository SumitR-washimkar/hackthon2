document.addEventListener('DOMContentLoaded', () => {
    console.log('Employee Dashboard loaded');

    // Navigation between sections (Home, Expenses)
    const navLinks = document.querySelectorAll('.nav-link');
    const sections = document.querySelectorAll('.section');

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

    // Tabs navigation (Uploaded, New)
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabContents = document.querySelectorAll('.tab-content');

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

    if (uploadBtn) {
        uploadBtn.addEventListener('click', async () => {
            const file = receiptUpload.files[0];
            
            if (!file) {
                alert('Please select an image file.');
                return;
            }

            // Validate file type
            const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/bmp', 'image/webp'];
            if (!validTypes.includes(file.type)) {
                alert('Please upload a valid image file (PNG, JPEG, GIF, BMP, WEBP)');
                return;
            }

            // Show loading
            uploadBtn.disabled = true;
            uploadBtn.textContent = 'Processing...';

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
                    // Populate form fields
                    document.getElementById('employee').value = result.data.employee || getUserName() || '';
                    document.getElementById('description').value = result.data.description || '';
                    document.getElementById('date').value = result.data.date || '';
                    document.getElementById('category').value = result.data.category || 'Other';
                    document.getElementById('paid_by').value = result.data.paid_by || 'Cash';
                    document.getElementById('remark').value = result.data.remark || '';
                    document.getElementById('amount').value = result.data.amount || '';
                    
                    // Show form
                    expenseForm.style.display = 'block';
                    
                    alert('Receipt processed successfully! Please verify the details.');
                } else {
                    throw new Error('No data extracted from receipt');
                }

            } catch (error) {
                console.error('OCR Error:', error);
                alert('Error: ' + error.message);
                // Show empty form for manual entry
                expenseForm.style.display = 'block';
            } finally {
                uploadBtn.disabled = false;
                uploadBtn.textContent = 'Upload and Extract';
            }
        });
    }

    // Submit expense form
    if (expenseForm) {
        expenseForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const expenseData = {
                employee: document.getElementById('employee').value,
                description: document.getElementById('description').value,
                date: document.getElementById('date').value,
                category: document.getElementById('category').value,
                paid_by: document.getElementById('paid_by').value,
                remark: document.getElementById('remark').value,
                amount: parseFloat(document.getElementById('amount').value),
                status: 'Pending',
                submitted: new Date().toISOString(),
                user_id: getUserId(),
                company_id: localStorage.getItem('company_id')
            };

            // Validate
            if (!expenseData.description || !expenseData.amount || !expenseData.date) {
                alert('Please fill in Description, Amount, and Date');
                return;
            }

            try {
                const response = await fetch('/api/expenses', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(expenseData)
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.detail || 'Failed to submit expense');
                }

                alert('Expense submitted successfully!');
                
                // Reset form
                expenseForm.reset();
                expenseForm.style.display = 'none';
                receiptUpload.value = '';

                // Switch to uploaded tab
                document.querySelector('.tab-link[data-tab="uploaded"]').click();

            } catch (error) {
                console.error('Submit Error:', error);
                alert('Error: ' + error.message);
            }
        });
    }

    // Load and display uploaded expenses
    async function loadUploadedExpenses() {
        const userId = getUserId();
        
        if (!userId) {
            console.error('No user ID found. Please login.');
            return;
        }

        console.log('Loading expenses for user:', userId);

        try {
            const response = await fetch(`/api/expenses?user_id=${userId}`);

            if (!response.ok) {
                throw new Error('Failed to fetch expenses');
            }

            const expenses = await response.json();
            console.log('Loaded expenses:', expenses);
            
            displayExpenses(expenses);

        } catch (error) {
            console.error('Error loading expenses:', error);
            displayExpenses([]);
        }
    }

    // Display expenses in the uploaded table
    function displayExpenses(expenses) {
        // Find the table body in the uploaded tab
        const uploadedTab = document.getElementById('uploaded');
        const tbody = uploadedTab.querySelector('tbody');
        
        if (!tbody) {
            console.error('Table body not found');
            return;
        }

        if (!expenses || expenses.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 20px;">No expenses found.</td></tr>';
            return;
        }

        tbody.innerHTML = expenses.map(expense => `
            <tr>
                <td>${formatDate(expense.date)}</td>
                <td>₹${parseFloat(expense.amount || 0).toFixed(2)}</td>
                <td>${expense.category || 'Other'}</td>
                <td><span class="status-${(expense.status || 'pending').toLowerCase()}">${expense.status || 'Pending'}</span></td>
            </tr>
        `).join('');
    }

    // Helper: Get user ID from localStorage
    function getUserId() {
        return localStorage.getItem('user_id');
    }

    // Helper: Get user name from localStorage
    function getUserName() {
        return localStorage.getItem('user_name');
    }

    // Helper: Format date
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

    // Load expenses when page loads
    loadUploadedExpenses();

    // Also load when navigating to expenses section
    const expensesNavLink = document.querySelector('.nav-link[data-section="expenses"]');
    if (expensesNavLink) {
        expensesNavLink.addEventListener('click', () => {
            setTimeout(() => {
                // Check if uploaded tab is active
                const uploadedTab = document.querySelector('.tab-link[data-tab="uploaded"]');
                if (uploadedTab && uploadedTab.classList.contains('active')) {
                    loadUploadedExpenses();
                }
            }, 100);
        });
    }
});