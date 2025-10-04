// Check authentication and role
const REQUIRED_ROLE = 'admin';

const token = localStorage.getItem('token');
const user = JSON.parse(localStorage.getItem('user') || '{}');

if (!token || user.role !== REQUIRED_ROLE) {
    alert('Unauthorized access. Admin role required.');
    window.location.href = '/login';
}

// Display user info
document.getElementById('adminName').textContent = user.name || 'Admin';
document.getElementById('userEmail').textContent = user.email || '';

// Navigation handler
const navItems = document.querySelectorAll('.nav-item');
const pages = document.querySelectorAll('.page-content');
const pageTitle = document.getElementById('pageTitle');

// Page titles mapping
const pageTitles = {
    'home': 'Dashboard',
    'create': 'Create Employee',
    'management': 'Expense Management'
};

// Handle navigation clicks
navItems.forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        
        const pageName = item.getAttribute('data-page');
        
        // Remove active class from all nav items
        navItems.forEach(nav => nav.classList.remove('active'));
        
        // Add active class to clicked item
        item.classList.add('active');
        
        // Hide all pages
        pages.forEach(page => page.classList.remove('active'));
        
        // Show selected page
        const selectedPage = document.getElementById(pageName + 'Page');
        if (selectedPage) {
            selectedPage.classList.add('active');
        }
        
        // Update page title
        pageTitle.textContent = pageTitles[pageName] || 'Dashboard';
        
        // Load content in iframe for create and management pages
        if (pageName === 'create') {
            const iframe = document.getElementById('createEmployeeFrame');
            // Always set src, even if already set (to force reload)
            iframe.src = '/admin_create';
            console.log('Loading admin_create page');
        } else if (pageName === 'management') {
            const iframe = document.getElementById('managementFrame');
            iframe.src = '/admin_expenses';
            console.log('Loading admin_expenses page');
        }
    });
});

// Logout handler
document.getElementById('logoutBtn').addEventListener('click', () => {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
    }
});

// Load dashboard statistics
function loadDashboardStats() {
    console.log('Dashboard loaded for user:', user);
}

// Initialize dashboard
loadDashboardStats();