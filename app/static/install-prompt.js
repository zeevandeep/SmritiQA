/**
 * PWA Install Prompt Manager
 * Handles the installation prompt for Progressive Web App
 */

class PWAInstallManager {
    constructor() {
        this.deferredPrompt = null;
        this.installButton = null;
        this.isInstalled = false;
        this.promptShown = false;
        
        this.init();
    }
    
    init() {
        // Check if already installed
        this.checkInstallStatus();
        
        // Listen for the beforeinstallprompt event
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('PWA install prompt available');
            // Prevent the mini-infobar from appearing on mobile
            e.preventDefault();
            // Save the event for later use
            this.deferredPrompt = e;
            // Show our custom install prompt
            this.showInstallPrompt();
        });
        
        // Listen for the app installed event
        window.addEventListener('appinstalled', () => {
            console.log('PWA was installed');
            this.handleAppInstalled();
        });
        
        // Check if launched as PWA
        if (window.matchMedia('(display-mode: standalone)').matches) {
            console.log('App is running in standalone mode');
            this.isInstalled = true;
        }
        
        // Create install UI after DOM is loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.createInstallUI());
        } else {
            this.createInstallUI();
        }
    }
    
    checkInstallStatus() {
        // Check if running as installed PWA
        if (window.navigator.standalone === true || 
            window.matchMedia('(display-mode: standalone)').matches ||
            document.referrer.includes('android-app://')) {
            this.isInstalled = true;
            return;
        }
        
        // Check localStorage for previous dismiss
        const dismissed = localStorage.getItem('pwa-install-dismissed');
        const dismissedTime = localStorage.getItem('pwa-install-dismissed-time');
        
        if (dismissed && dismissedTime) {
            const daysSinceDismiss = (Date.now() - parseInt(dismissedTime)) / (1000 * 60 * 60 * 24);
            if (daysSinceDismiss < 7) { // Don't show again for 7 days
                return;
            }
        }
    }
    
    createInstallUI() {
        // Create install banner HTML
        const installBanner = document.createElement('div');
        installBanner.id = 'pwa-install-banner';
        installBanner.className = 'pwa-install-banner';
        installBanner.style.display = 'none';
        
        installBanner.innerHTML = `
            <div class="install-content">
                <div class="install-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z" fill="currentColor"/>
                    </svg>
                </div>
                <div class="install-text">
                    <div class="install-title">Install Smriti</div>
                    <div class="install-subtitle">Get the full app experience</div>
                </div>
                <div class="install-actions">
                    <button class="install-btn-install" id="pwa-install-btn">Install</button>
                    <button class="install-btn-dismiss" id="pwa-dismiss-btn">×</button>
                </div>
            </div>
        `;
        
        // Add CSS styles
        const style = document.createElement('style');
        style.textContent = `
            .pwa-install-banner {
                position: fixed;
                bottom: 20px;
                left: 20px;
                right: 20px;
                background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
                color: white;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
                z-index: 9999;
                animation: slideUp 0.3s ease-out;
                max-width: 400px;
                margin: 0 auto;
            }
            
            @keyframes slideUp {
                from {
                    transform: translateY(100%);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }
            
            .install-content {
                display: flex;
                align-items: center;
                padding: 16px;
                gap: 12px;
            }
            
            .install-icon {
                flex-shrink: 0;
                width: 40px;
                height: 40px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .install-text {
                flex: 1;
                min-width: 0;
            }
            
            .install-title {
                font-weight: 600;
                font-size: 16px;
                margin-bottom: 2px;
            }
            
            .install-subtitle {
                font-size: 14px;
                opacity: 0.9;
            }
            
            .install-actions {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .install-btn-install {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .install-btn-install:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            
            .install-btn-dismiss {
                background: none;
                border: none;
                color: white;
                font-size: 20px;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.2s ease;
            }
            
            .install-btn-dismiss:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            
            /* Hide on very small screens */
            @media (max-width: 360px) {
                .pwa-install-banner {
                    left: 10px;
                    right: 10px;
                    bottom: 10px;
                }
                
                .install-content {
                    padding: 12px;
                }
                
                .install-title {
                    font-size: 15px;
                }
                
                .install-subtitle {
                    font-size: 13px;
                }
            }
        `;
        
        // Append to document
        document.head.appendChild(style);
        document.body.appendChild(installBanner);
        
        // Store references
        this.installBanner = installBanner;
        this.installButton = document.getElementById('pwa-install-btn');
        
        // Add event listeners
        this.installButton.addEventListener('click', () => this.handleInstallClick());
        document.getElementById('pwa-dismiss-btn').addEventListener('click', () => this.dismissPrompt());
    }
    
    showInstallPrompt() {
        if (this.isInstalled || this.promptShown) {
            return;
        }
        
        // Show after a delay to avoid interrupting user
        setTimeout(() => {
            if (this.installBanner) {
                this.installBanner.style.display = 'block';
                this.promptShown = true;
                
                // Track in analytics if available
                if (window.gtag) {
                    gtag('event', 'pwa_prompt_shown', {
                        event_category: 'PWA',
                        event_label: 'Install Prompt Shown'
                    });
                }
            }
        }, 3000); // Show after 3 seconds
    }
    
    async handleInstallClick() {
        if (!this.deferredPrompt) {
            // Fallback for browsers that don't support beforeinstallprompt
            this.showManualInstallInstructions();
            return;
        }
        
        try {
            // Show the install prompt
            this.deferredPrompt.prompt();
            
            // Wait for user response
            const { outcome } = await this.deferredPrompt.userChoice;
            
            console.log(`User response to install prompt: ${outcome}`);
            
            // Track user choice
            if (window.gtag) {
                gtag('event', 'pwa_install_response', {
                    event_category: 'PWA',
                    event_label: outcome,
                    value: outcome === 'accepted' ? 1 : 0
                });
            }
            
            if (outcome === 'accepted') {
                console.log('User accepted the install prompt');
            } else {
                console.log('User dismissed the install prompt');
                this.dismissPrompt();
            }
            
            // Clear the saved prompt
            this.deferredPrompt = null;
            
        } catch (error) {
            console.error('Error during install:', error);
            this.showManualInstallInstructions();
        }
    }
    
    showManualInstallInstructions() {
        const userAgent = navigator.userAgent.toLowerCase();
        let instructions = '';
        
        if (userAgent.includes('chrome') && userAgent.includes('mobile')) {
            instructions = 'Tap the menu (⋮) and select "Add to Home screen"';
        } else if (userAgent.includes('safari') && userAgent.includes('mobile')) {
            instructions = 'Tap the share button (⬆) and select "Add to Home Screen"';
        } else if (userAgent.includes('firefox')) {
            instructions = 'Tap the menu and select "Install"';
        } else {
            instructions = 'Look for "Add to Home Screen" or "Install" in your browser menu';
        }
        
        // Create temporary notification
        this.showInstallToast(`To install: ${instructions}`);
    }
    
    showInstallToast(message) {
        const toast = document.createElement('div');
        toast.className = 'pwa-install-toast';
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: #333;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 10000;
            max-width: 90%;
            text-align: center;
            animation: slideDown 0.3s ease-out;
        `;
        
        const slideDownStyle = document.createElement('style');
        slideDownStyle.textContent = `
            @keyframes slideDown {
                from { transform: translateX(-50%) translateY(-100%); opacity: 0; }
                to { transform: translateX(-50%) translateY(0); opacity: 1; }
            }
        `;
        document.head.appendChild(slideDownStyle);
        
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
            slideDownStyle.remove();
        }, 5000);
    }
    
    dismissPrompt() {
        if (this.installBanner) {
            this.installBanner.style.display = 'none';
        }
        
        // Remember dismissal
        localStorage.setItem('pwa-install-dismissed', 'true');
        localStorage.setItem('pwa-install-dismissed-time', Date.now().toString());
        
        // Track dismissal
        if (window.gtag) {
            gtag('event', 'pwa_prompt_dismissed', {
                event_category: 'PWA',
                event_label: 'Install Prompt Dismissed'
            });
        }
    }
    
    handleAppInstalled() {
        this.isInstalled = true;
        
        if (this.installBanner) {
            this.installBanner.style.display = 'none';
        }
        
        // Clear dismissal flags
        localStorage.removeItem('pwa-install-dismissed');
        localStorage.removeItem('pwa-install-dismissed-time');
        
        // Show success message
        this.showInstallToast('Smriti installed successfully! 🎉');
        
        // Track installation
        if (window.gtag) {
            gtag('event', 'pwa_installed', {
                event_category: 'PWA',
                event_label: 'App Installed Successfully'
            });
        }
    }
}

// Initialize when script loads
window.pwaInstallManager = new PWAInstallManager();