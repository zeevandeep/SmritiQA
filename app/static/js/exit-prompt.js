/**
 * Press Back Again to Exit Functionality for Smriti PWA
 * 
 * Intercepts ALL back button presses on ANY page to show exit prompt first.
 * No navigation happens on first back press - only shows toast.
 * Second back press within 2 seconds exits the app.
 */

let backPressedOnce = false;
let backPressTimer = null;

// Push a dummy state to trap back presses
history.pushState(null, null, location.href);

// Listen for back/forward navigation
window.addEventListener("popstate", function (event) {
    if (backPressedOnce) {
        // Second back press - exit the app
        clearTimeout(backPressTimer);
        removeExitToast();
        
        // Try to close the app (works in PWA standalone mode)
        if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone) {
            window.close(); // For PWA
        } else {
            history.go(-2); // Browser fallback
        }
    } else {
        // First back press - show toast and prevent navigation
        showExitToast();
        backPressedOnce = true;

        // Prevent navigation by pushing dummy state again
        history.pushState(null, null, location.href);

        // Reset after 2 seconds
        backPressTimer = setTimeout(() => {
            backPressedOnce = false;
            removeExitToast();
        }, 2000);
    }
});

// Display exit toast with Smriti orange theme
function showExitToast() {
    if (document.getElementById('exit-toast')) return;

    const toast = document.createElement('div');
    toast.id = 'exit-toast';
    toast.textContent = 'Press back again to exit Smriti';
    toast.style.cssText = `
        position: fixed;
        bottom: 60px;
        left: 50%;
        transform: translateX(-50%);
        background-color: var(--primary-color, #e67e22);
        color: white;
        padding: 12px 24px;
        border-radius: 25px;
        font-size: 15px;
        font-weight: 500;
        z-index: 9999;
        transition: opacity 0.3s ease-in-out;
        opacity: 1;
        box-shadow: 0 4px 15px rgba(230, 126, 34, 0.3);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;

    document.body.appendChild(toast);
}

// Remove exit toast
function removeExitToast() {
    const toast = document.getElementById('exit-toast');
    if (toast) {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }
}