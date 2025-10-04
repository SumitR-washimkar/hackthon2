// API Configuration
const API_CONFIG = {
    BASE_URL: window.location.origin,
    API_PREFIX: '/api',
    ENDPOINTS: {
        SIGNUP: '/api/signup',
        LOGIN: '/api/login',
        LOGOUT: '/api/logout',
        // Add more endpoints as needed
    }
};

// Get full API URL
function getApiUrl(endpoint) {
    return `${API_CONFIG.BASE_URL}${endpoint}`;
}

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { API_CONFIG, getApiUrl };
}