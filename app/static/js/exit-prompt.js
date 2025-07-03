/**
 * Press Back Again to Exit Functionality for Smriti PWA
 * 
 * Robust implementation that handles back button across different mobile environments.
 * Uses multiple detection methods for maximum compatibility.
 */

let backPressedOnce = false;
let backPressTimer = null;

// Debug function to track events
function debugLog(message) {
    console.log('[Exit Prompt]', message);
}

// Display exit toast with Smriti orange theme
function showExitToast() {
    debugLog('Showing exit toast');
    
    // Remove existing toast first
    const existingToast = document.getElementById('exit-toast');
    if (existingToast) {
        existingToast.remove();
    }

    const toast = document.createElement('div');
    toast.id = 'exit-toast';
    toast.textContent = 'Press back again to exit Smriti';
    toast.style.cssText = `
        position: fixed;
        bottom: 80px;
        left: 50%;
        transform: translateX(-50%);
        background-color: #e67e22;
        color: white;
        padding: 12px 24px;
        border-radius: 25px;
        font-size: 15px;
        font-weight: 500;
        z-index: 10000;
        transition: opacity 0.3s ease-in-out;
        opacity: 1;
        box-shadow: 0 4px 15px rgba(230, 126, 34, 0.3);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        text-align: center;
        min-width: 250px;
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

// Handle back press logic
function handleBackPress(event) {
    debugLog('Back press detected, backPressedOnce:', backPressedOnce);
    
    if (backPressedOnce) {
        // Second back press - exit the app
        debugLog('Second back press - attempting to exit');
        clearTimeout(backPressTimer);
        removeExitToast();
        
        // Try to close the app (multiple approaches)
        if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone) {
            debugLog('PWA mode detected - calling window.close()');
            window.close();
        } else {
            debugLog('Browser mode - attempting history navigation');
            // In browser mode, go back multiple steps
            try {
                history.go(-10); // Go back many steps to exit
            } catch (e) {
                window.close(); // Fallback
            }
        }
        return false;
    } else {
        // First back press - show toast and prevent navigation
        debugLog('First back press - showing toast');
        
        // Prevent the default back navigation
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }
        
        showExitToast();
        backPressedOnce = true;

        // Reset after 2 seconds
        backPressTimer = setTimeout(() => {
            debugLog('Timer expired - resetting state');
            backPressedOnce = false;
            removeExitToast();
        }, 2000);
        
        return false;
    }
}

// Initialize when DOM is ready
function initializeExitPrompt() {
    debugLog('Initializing exit prompt');
    
    // Method 1: More aggressive popstate handling
    let initialState = { page: 'current' };
    history.replaceState(initialState, null, location.href);
    
    // Push multiple dummy states to create a "buffer"
    for (let i = 0; i < 3; i++) {
        history.pushState({ page: 'exit-buffer-' + i }, null, location.href);
    }
    
    window.addEventListener('popstate', function(event) {
        debugLog('Popstate event triggered with state:', event.state);
        
        // Always handle as exit attempt
        if (handleBackPress(event) === false) {
            // Re-push buffer states
            for (let i = 0; i < 3; i++) {
                history.pushState({ page: 'exit-buffer-' + i }, null, location.href);
            }
        }
    });
    
    // Method 2: Beforeunload event (catches browser back/close)
    window.addEventListener('beforeunload', function(event) {
        debugLog('Beforeunload event triggered');
        if (!backPressedOnce) {
            event.preventDefault();
            event.returnValue = 'Press back again to exit Smriti';
            showExitToast();
            backPressedOnce = true;
            
            // Reset after 2 seconds
            backPressTimer = setTimeout(() => {
                debugLog('Timer expired - resetting state');
                backPressedOnce = false;
                removeExitToast();
            }, 2000);
            
            return 'Press back again to exit Smriti';
        }
    });
    
    // Method 3: Android back button (for Cordova/PhoneGap apps)
    document.addEventListener('backbutton', function(event) {
        debugLog('Android backbutton event triggered');
        handleBackPress(event);
    }, false);
    
    // Method 4: Keyboard back (ESC key as fallback)
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' || event.keyCode === 27) {
            debugLog('Escape key pressed - treating as back');
            handleBackPress(event);
        }
    });
    
    // Method 5: Page visibility change (detect when user navigates away)
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            debugLog('Page visibility changed - hidden');
            // Don't prevent this, but log it
        }
    });
    
    debugLog('Exit prompt initialized successfully with enhanced methods');
}

// Initialize when DOM loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeExitPrompt);
} else {
    initializeExitPrompt();
}