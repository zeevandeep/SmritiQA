/**
 * Press Back Again to Exit Functionality for Smriti PWA
 * 
 * Intercepts ALL back button presses on ANY page to show exit prompt first.
 * No navigation happens on first back press - only shows toast.
 * Second back press within 2 seconds exits the app.
 */

let backPressedOnce = false;
let backToastTimer = null;

// Push dummy history state when page loads
window.addEventListener('load', () => {
    console.log('[Exit Prompt] Initializing exit prompt on page load');
    history.pushState(null, '', location.href);
    console.log('[Exit Prompt] Exit prompt initialized successfully');
});

window.addEventListener('popstate', (event) => {
    console.log('[Exit Prompt] Back button pressed, backPressedOnce:', backPressedOnce);
    if (backPressedOnce) {
        // Second back press within timeout
        console.log('[Exit Prompt] Second back press - attempting to exit');
        if (window.matchMedia('(display-mode: standalone)').matches) {
            window.close(); // For PWA mode (Android only)
        } else {
            history.go(-2); // Tries to exit web session
        }
    } else {
        backPressedOnce = true;
        console.log('[Exit Prompt] First back press - showing toast');
        showExitToast();

        history.pushState(null, '', location.href); // Re-push dummy state

        backToastTimer = setTimeout(() => {
            backPressedOnce = false;
            console.log('[Exit Prompt] Timer expired - reset backPressedOnce');
        }, 2000); // 2 seconds to tap again
    }
});

// Cancel prompt if user interacts again (tap anywhere, scroll, etc.)
['click', 'touchstart', 'keydown', 'scroll'].forEach(eventType => {
    window.addEventListener(eventType, () => {
        if (backPressedOnce) {
            clearTimeout(backToastTimer);
            backPressedOnce = false;
            removeExitToast();
        }
    });
});

// Styled exit toast for Smriti (orange theme, clean typography)
function showExitToast() {
    let toast = document.getElementById('exit-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'exit-toast';
        toast.innerText = 'Press back again to exit Smriti';
        toast.style.position = 'fixed';
        toast.style.bottom = '70px';
        toast.style.left = '50%';
        toast.style.transform = 'translateX(-50%)';
        toast.style.background = 'var(--primary-color, #e67e22)';  // Smriti's orange tone
        toast.style.color = '#fff';
        toast.style.padding = '12px 24px';
        toast.style.borderRadius = '999px';
        toast.style.boxShadow = '0 4px 15px rgba(230, 126, 34, 0.3)';
        toast.style.fontFamily = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        toast.style.fontWeight = '500';
        toast.style.fontSize = '14px';
        toast.style.letterSpacing = '0.3px';
        toast.style.zIndex = '9999';
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease-in-out';
        document.body.appendChild(toast);
    }

    toast.style.opacity = '1';
    setTimeout(() => {
        toast.style.opacity = '0';
    }, 1800);
}

// Remove exit toast
function removeExitToast() {
    const toast = document.getElementById('exit-toast');
    if (toast) {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }
}