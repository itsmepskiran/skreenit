// Final fallback to new public APIs (Render primary, Railway secondary)
if (!deduped.length) {
  deduped.push('https://aiskreenit.onrender.com')
  deduped.push('https://skreenit.up.railway.app')
}

// Create a complete backend client with proper failover logic for local and production environments
class BackendClient {
    constructor() {
        this.backendUrls = this.getBackendUrls();
        this.currentUrlIndex = 0;
        this.requestTimeout = 10000; // 10 seconds
        this.maxRetries = 3;
    }

    /**
     * Get backend URLs based on environment
     */
    getBackendUrls() {
        const host = window.location.hostname || '';
        const isLocal = host === 'localhost' || host === '127.0.0.1' || host === '';

        if (isLocal) {
            // Local development
            return [
                'http://localhost:8000'
            ];
        } else {
            // Production with failover
            return [
                'https://aiskreenit.onrender.com',
                'https://skreenit.up.railway.app'
            ];
        }
    }

    /**
     * Get current backend URL
     */
    getCurrentUrl() {
        return this.backendUrls[this.currentUrlIndex];
    }

    /**
     * Switch to next backend URL (failover)
     */
    switchToNextUrl() {
        this.currentUrlIndex = (this.currentUrlIndex + 1) % this.backendUrls.length;
        console.log(`Switched to backend URL: ${this.getCurrentUrl()}`);
    }

    /**
     * Make HTTP request with automatic failover
     */
    async request(endpoint, options = {}) {
        const maxAttempts = Math.min(this.maxRetries + 1, this.backendUrls.length);
        let lastError;

        for (let attempt = 0; attempt < maxAttempts; attempt++) {
            const url = `${this.getCurrentUrl()}${endpoint}`;

            try {
                console.log(`Attempting request to: ${url} (attempt ${attempt + 1}/${maxAttempts})`);

                const response = await fetch(url, {
                    timeout: this.requestTimeout,
                    headers: {
                        'Content-Type': 'application/json',
                        ...options.headers,
                    },
                    ...options
                });

                // If we get a 5xx error, try next backend
                if (response.status >= 500) {
                    throw new Error(`Server error: ${response.status}`);
                }

                // If we get a 4xx error (except 401, 403 which are auth issues), try next backend
                if (response.status >= 400 && response.status !== 401 && response.status !== 403) {
                    throw new Error(`Client error: ${response.status}`);
                }

                return response;

            } catch (error) {
                console.warn(`Request failed for ${url}:`, error.message);
                lastError = error;

                // If this isn't the last attempt, switch to next URL
                if (attempt < maxAttempts - 1) {
                    this.switchToNextUrl();
                }
            }
        }

        // All backends failed
        throw new Error(`All backend servers failed. Last error: ${lastError.message}`);
    }

    /**
     * GET request
     */
    async get(endpoint, options = {}) {
        return this.request(endpoint, { method: 'GET', ...options });
    }

    /**
     * POST request
     */
    async post(endpoint, data = null, options = {}) {
        const requestOptions = {
            method: 'POST',
            body: data ? JSON.stringify(data) : null,
            ...options
        };

        return this.request(endpoint, requestOptions);
    }

    /**
     * PUT request
     */
    async put(endpoint, data = null, options = {}) {
        const requestOptions = {
            method: 'PUT',
            body: data ? JSON.stringify(data) : null,
            ...options
        };

        return this.request(endpoint, requestOptions);
    }

    /**
     * DELETE request
     */
    async delete(endpoint, options = {}) {
        return this.request(endpoint, { method: 'DELETE', ...options });
    }

    /**
     * Upload file with FormData
     */
    async uploadFile(endpoint, formData, options = {}) {
        const requestOptions = {
            method: 'POST',
            body: formData,
            ...options
        };

        // Don't set Content-Type for FormData - browser will set it with boundary
        return this.request(endpoint, requestOptions);
    }

    /**
     * Health check for current backend
     */
    async healthCheck() {
        try {
            const response = await this.get('/health', { timeout: 5000 });
            return response.ok;
        } catch (error) {
            console.warn(`Health check failed for ${this.getCurrentUrl()}:`, error.message);
            return false;
        }
    }

    /**
     * Get backend status for all URLs
     */
    async getAllBackendStatus() {
        const status = {};

        for (let i = 0; i < this.backendUrls.length; i++) {
            const originalIndex = this.currentUrlIndex;
            this.currentUrlIndex = i;

            try {
                const isHealthy = await this.healthCheck();
                status[this.backendUrls[i]] = {
                    healthy: isHealthy,
                    responseTime: isHealthy ? 'OK' : 'FAILED'
                };
            } catch (error) {
                status[this.backendUrls[i]] = {
                    healthy: false,
                    error: error.message
                };
            }

            this.currentUrlIndex = originalIndex;
        }

        return status;
    }
}

// Create global instance
const backendClient = new BackendClient();

// Export functions for easy use
export const backendFetch = async (endpoint, options = {}) => {
    return backendClient.request(endpoint, options);
};

export const backendGet = async (endpoint, options = {}) => {
    return backendClient.get(endpoint, options);
};

export const backendPost = async (endpoint, data = null, options = {}) => {
    return backendClient.post(endpoint, data, options);
};

export const backendPut = async (endpoint, data = null, options = {}) => {
    return backendClient.put(endpoint, data, options);
};

export const backendDelete = async (endpoint, options = {}) => {
    return backendClient.delete(endpoint, options);
};

export const backendUploadFile = async (endpoint, formData, options = {}) => {
    return backendClient.uploadFile(endpoint, formData, options);
};

export const backendUrl = () => {
    return backendClient.getCurrentUrl();
};

export const backendHealth = async () => {
    return backendClient.healthCheck();
};

export const backendStatus = async () => {
    return backendClient.getAllBackendStatus();
};

// Global error handler for unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection in backend client:', event.reason);
    // Optionally show user-friendly error message
});

// Export the client instance for advanced usage
export { backendClient };

// Utility function to handle common response patterns
export const handleResponse = async (response) => {
    if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`;

        try {
            const errorData = await response.json();
            errorMessage = errorData.error || errorData.message || errorMessage;
        } catch (e) {
            // If we can't parse JSON, use status text
            errorMessage = response.statusText || errorMessage;
        }

        throw new Error(errorMessage);
    }

    try {
        return await response.json();
    } catch (e) {
        // If response is not JSON, return text
        return await response.text();
    }
};

// Usage examples:
// const data = await backendGet('/api/jobs');
// const result = await backendPost('/api/apply', applicationData);
// const uploadResult = await backendUploadFile('/api/upload-resume', formData);
