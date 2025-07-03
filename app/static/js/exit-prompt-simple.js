/**
 * Simple and Direct Exit Prompt for Smriti PWA
 * 
 * This approach tries to be as direct as possible about preventing navigation
 */

(function() {
    'use strict';
    
    let backPressedOnce = false;
    let backPressTimer = null;
    
    function log(message) {
        console.log('[Exit Prompt Simple]', message);
    }
    
    function showExitToast() {
        log('Showing exit toast');
        
        // Remove existing toast
        const existingToast = document.getElementById('exit-toast-simple');
        if (existingToast) {
            existingToast.remove();
        }
        
        const toast = document.createElement('div');
        toast.id = 'exit-toast-simple';
        toast.innerHTML = '<strong>Press back again to exit Smriti</strong>';
        toast.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: #e67e22;
            color: white;
            padding: 20px 30px;
            border-radius: 15px;
            font-size: 16px;
            font-weight: bold;
            z-index: 99999;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            text-align: center;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            animation: fadeIn 0.3s ease-in-out;
        `;
        
        // Add CSS animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeIn {
                from { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
                to { opacity: 1; transform: translate(-50%, -50%) scale(1); }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(toast);
        
        // Auto-remove after 2 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.style.animation = 'fadeIn 0.3s ease-in-out reverse';
                setTimeout(() => toast.remove(), 300);
            }
        }, 2000);
    }
    
    function handleExitAttempt() {
        log('Exit attempt detected. backPressedOnce:', backPressedOnce);
        
        if (backPressedOnce) {
            log('Second attempt - allowing exit');
            clearTimeout(backPressTimer);
            
            // Try multiple exit strategies
            if (window.close) {
                window.close();
            }
            
            // If still here, try going back in history
            setTimeout(() => {
                try {
                    history.go(-5);
                } catch (e) {
                    log('History navigation failed, trying location change');
                    window.location.href = 'about:blank';
                }
            }, 100);
            
            return true; // Allow exit
        } else {
            log('First attempt - showing toast');
            backPressedOnce = true;
            showExitToast();
            
            // Reset after 2 seconds
            backPressTimer = setTimeout(() => {
                log('Resetting exit state');
                backPressedOnce = false;
            }, 2000);
            
            return false; // Prevent exit
        }
    }
    
    // Initialize
    function init() {
        log('Initializing simple exit prompt');
        
        // Create buffer in history
        history.pushState({ exitPrompt: true }, '', location.href);
        
        // Listen for popstate
        window.addEventListener('popstate', function(event) {
            log('Popstate triggered:', event.state);
            
            if (!handleExitAttempt()) {
                // Prevent navigation by re-pushing state
                history.pushState({ exitPrompt: true }, '', location.href);
            }
        });
        
        // Also try to catch beforeunload as backup
        window.addEventListener('beforeunload', function(event) {
            log('Beforeunload triggered');
            if (!backPressedOnce) {
                const message = 'Press back again to exit Smriti';
                event.returnValue = message;
                handleExitAttempt();
                return message;
            }
        });
        
        log('Simple exit prompt initialized');
    }
    
    // Initialize when ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();