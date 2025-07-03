/**
 * Press Back Again to Exit Functionality for Smriti PWA
 * 
 * Implements native mobile app-like exit behavior where pressing back button
 * shows a toast "Press back again to exit Smriti" and exits on second press.
 */

let exitPromptActive = false;
let exitPromptTimeout = null;

function showExitToast() {
    // Create toast if it doesn't exist
    if (!document.getElementById('exit-toast')) {
        const toast = document.createElement('div');
        toast.id = 'exit-toast';
        toast.innerText = 'Press back again to exit Smriti';
        toast.style.cssText = `
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            background-color: var(--primary-color, #e67e22);
            color: white;
            padding: 12px 20px;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 500;
            z-index: 9999;
            transition: opacity 0.3s ease-in-out;
            opacity: 0;
            box-shadow: 0 4px 15px rgba(230, 126, 34, 0.3);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;
        document.body.appendChild(toast);
        
        // Fade in the toast
        setTimeout(() => { 
            toast.style.opacity = 1; 
        }, 50);
    }

    exitPromptActive = true;

    // Remove toast and reset after 2 seconds
    exitPromptTimeout = setTimeout(() => {
        exitPromptActive = false;
        const toast = document.getElementById('exit-toast');
        if (toast) {
            toast.style.opacity = 0;
            setTimeout(() => toast.remove(), 300);
        }
    }, 2000);
}

function tryExitApp() {
    // Clear any existing timeout
    if (exitPromptTimeout) {
        clearTimeout(exitPromptTimeout);
    }
    
    // Remove toast immediately
    const toast = document.getElementById('exit-toast');
    if (toast) {
        toast.remove();
    }
    
    // Try to close the app/tab (works in standalone PWA mode)
    window.close();
    
    // Fallback: Navigate back if window.close() doesn't work
    history.back();
}

document.addEventListener('DOMContentLoaded', () => {
    // Push a dummy state so we can catch the first back press
    history.pushState(null, null, location.href);

    window.addEventListener('popstate', (event) => {
        if (exitPromptActive) {
            // Second back press within 2 seconds - exit the app
            tryExitApp();
        } else {
            // First back press - show exit prompt
            showExitToast();
            // Re-push the dummy state to prevent real navigation
            history.pushState(null, null, location.href);
        }
    });
});