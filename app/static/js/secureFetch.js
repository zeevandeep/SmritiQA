/**
 * Secure fetch wrapper with automatic token refresh capability.
 * Handles 401 errors by attempting token refresh and retrying the original request.
 */

let isRefreshing = false;
let refreshPromise = null;

async function secureFetch(url, options = {}) {
    // Ensure credentials are included for cookie-based auth
    const requestOptions = {
        ...options,
        credentials: 'include'
    };
    
    let response = await fetch(url, requestOptions);
    
    // Handle 401 Unauthorized (token expired)
    if (response.status === 401) {
        console.warn("Access token expired or invalid – attempting refresh.");
        
        // Prevent multiple concurrent refresh attempts
        if (!isRefreshing) {
            isRefreshing = true;
            refreshPromise = fetch('/api/v1/auth/refresh', {
                method: 'POST',
                credentials: 'include'
            }).finally(() => {
                isRefreshing = false;
                refreshPromise = null;
            });
        }
        
        try {
            const refreshRes = await refreshPromise;
            
            if (!refreshRes.ok) {
                // Refresh failed - redirect to login
                console.error("Token refresh failed. Redirecting to login.");
                alert("Session expired. Please log in again.");
                window.location.href = "/login";
                return;
            }
            
            console.log("Token refresh successful. Retrying original request.");
            // Retry the original request with new token
            response = await fetch(url, requestOptions);
            
        } catch (error) {
            // Network error during refresh
            console.warn("Network error during token refresh:", error);
            alert("Connection issue. Please refresh the page or log in again.");
            window.location.href = "/login";
            return;
        }
    }
    
    return response;
}

// Make secureFetch globally available
window.secureFetch = secureFetch;