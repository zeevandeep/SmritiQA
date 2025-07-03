/**
 * Dual-Platform PWA Install Prompt Manager
 * Provides consistent install experience across Android (native) and iOS (manual guidance)
 */

class PWAInstallManager {
    constructor() {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.promptShown = false;
        this.platform = this.detectPlatform();
        this.engagementTimer = null;
        this.userEngaged = false;
        
        this.init();
    }
    
    detectPlatform() {
        const userAgent = navigator.userAgent.toLowerCase();
        const isIOS = /ipad|iphone|ipod/.test(userAgent) && !window.MSStream;
        const isIOSChrome = isIOS && /crios/.test(userAgent);
        const isIOSSafari = isIOS && /safari/.test(userAgent) && !/crios/.test(userAgent);
        const isAndroid = /android/.test(userAgent);
        const supportsBeforeInstallPrompt = 'onbeforeinstallprompt' in window;
        
        return {
            isIOS,
            isIOSChrome,
            isIOSSafari,
            isAndroid,
            supportsBeforeInstallPrompt,
            browserName: this.getBrowserName(userAgent)
        };
    }
    
    getBrowserName(userAgent) {
        if (userAgent.includes('crios')) return 'Chrome';
        if (userAgent.includes('safari') && !userAgent.includes('chrome')) return 'Safari';
        if (userAgent.includes('chrome')) return 'Chrome';
        if (userAgent.includes('firefox')) return 'Firefox';
        if (userAgent.includes('edge')) return 'Edge';
        return 'Unknown';
    }
    
    init() {
        console.log('PWA Install Manager initialized for platform:', this.platform);
        
        // Check if already installed
        this.checkInstallStatus();
        
        if (this.isInstalled) {
            console.log('PWA already installed, skipping prompts');
            return;
        }
        
        // Set up platform-specific handling
        if (this.platform.supportsBeforeInstallPrompt) {
            this.setupAndroidFlow();
        } else if (this.platform.isIOS) {
            this.setupIOSFlow();
        }
        
        // Create install UI after DOM is loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.createInstallUI());
        } else {
            this.createInstallUI();
        }
        
        // Track user engagement for iOS prompt timing
        this.trackUserEngagement();
    }
    
    setupAndroidFlow() {
        // Listen for the beforeinstallprompt event (Android/Chrome)
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('PWA install prompt available (Android)');
            e.preventDefault();
            this.deferredPrompt = e;
            this.schedulePromptDisplay();
        });
        
        // Listen for app installed event
        window.addEventListener('appinstalled', () => {
            console.log('PWA was installed (Android)');
            this.handleAppInstalled();
        });
    }
    
    setupIOSFlow() {
        // For iOS, we'll show the prompt after user engagement
        console.log('Setting up iOS install flow');
        // Force show for iOS testing
        if (this.platform.isIOS) {
            console.log('iOS detected - will show prompt immediately for testing');
            setTimeout(() => {
                this.showInstallPrompt();
            }, 2000);
        }
        this.scheduleIOSPrompt();
    }
    
    trackUserEngagement() {
        const engagementEvents = ['scroll', 'click', 'touch', 'keydown'];
        
        const handleEngagement = () => {
            if (!this.userEngaged) {
                this.userEngaged = true;
                console.log('User engagement detected');
                
                // Remove listeners after first engagement
                engagementEvents.forEach(event => {
                    document.removeEventListener(event, handleEngagement);
                });
            }
        };
        
        engagementEvents.forEach(event => {
            document.addEventListener(event, handleEngagement, { passive: true });
        });
    }
    
    schedulePromptDisplay() {
        // Show prompt after engagement + delay
        console.log('schedulePromptDisplay called, platform isIOS:', this.platform.isIOS, 'userEngaged:', this.userEngaged);
        
        if (this.engagementTimer) {
            clearTimeout(this.engagementTimer);
        }
        
        this.engagementTimer = setTimeout(() => {
            console.log('Prompt display timer triggered. iOS:', this.platform.isIOS, 'Engaged:', this.userEngaged, 'Already shown:', this.promptShown);
            if (this.userEngaged || this.platform.isIOS) {
                this.showInstallPrompt();
            } else {
                console.log('Not showing prompt - waiting for user engagement');
            }
        }, 3000);
    }
    
    scheduleIOSPrompt() {
        // For iOS, show prompt after user engagement + delay
        console.log('Scheduling iOS prompt display');
        setTimeout(() => {
            console.log('iOS prompt timer triggered, user engaged:', this.userEngaged);
            this.schedulePromptDisplay();
        }, 1000);
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
                this.promptShown = true; // Prevent showing
                return;
            }
        }
    }
    
    createInstallUI() {
        // Create the main install popup modal
        this.createInstallModal();
        
        // Create iOS instruction modal if needed
        if (this.platform.isIOS) {
            this.createIOSInstructionModal();
        }
    }
    
    createInstallModal() {
        // Create install popup modal (similar to Android native prompt)
        const installModal = document.createElement('div');
        installModal.id = 'pwa-install-modal';
        installModal.className = 'pwa-install-modal';
        installModal.style.display = 'none';
        
        const appIcon = '/static/icon-192.png';
        const isIOSDevice = this.platform.isIOS;
        const buttonText = isIOSDevice ? 'Show Instructions' : 'Install';
        
        installModal.innerHTML = `
            <div class="install-modal-overlay">
                <div class="install-modal-content">
                    <div class="install-modal-header">
                        <img src="${appIcon}" alt="Smriti" class="install-app-icon">
                        <div class="install-app-info">
                            <h3 class="install-app-name">Smriti</h3>
                            <p class="install-app-url">${window.location.hostname}</p>
                        </div>
                        <button class="install-close-btn" id="pwa-modal-close">×</button>
                    </div>
                    <div class="install-modal-body">
                        <p class="install-description">
                            ${isIOSDevice ? 
                                'Add Smriti to your home screen for quick access and a better experience.' :
                                'Install Smriti for faster loading, offline access, and a native app experience.'
                            }
                        </p>
                        <div class="install-features">
                            <div class="install-feature">
                                <span class="install-feature-icon">⚡</span>
                                <span>Faster loading</span>
                            </div>
                            <div class="install-feature">
                                <span class="install-feature-icon">📱</span>
                                <span>Works offline</span>
                            </div>
                            <div class="install-feature">
                                <span class="install-feature-icon">🏠</span>
                                <span>Home screen access</span>
                            </div>
                        </div>
                    </div>
                    <div class="install-modal-actions">
                        <button class="install-btn-cancel" id="pwa-modal-cancel">Not now</button>
                        <button class="install-btn-primary" id="pwa-modal-install">${buttonText}</button>
                    </div>
                </div>
            </div>
        `;
        
        // Store reference and add event listeners
        this.installModal = installModal;
        this.setupModalEventListeners();
        
        // Add CSS styles for modal
        this.addModalStyles();
        
        // Append to document
        document.body.appendChild(installModal);
        
        // Add iOS testing support
        if (this.platform.isIOS) {
            this.addIOSTestButton();
        }
    }
    
    createIOSInstructionModal() {
        // Create iOS-specific instruction modal
        const instructionModal = document.createElement('div');
        instructionModal.id = 'pwa-ios-instructions';
        instructionModal.className = 'pwa-ios-instructions';
        instructionModal.style.display = 'none';
        
        const browserName = this.platform.browserName;
        const isSafari = this.platform.isIOSSafari;
        
        const instructionSteps = isSafari ? [
            { step: 1, text: 'Tap the Share button', icon: '⬆️', detail: 'Look for the share icon at the bottom of Safari' },
            { step: 2, text: 'Scroll down and tap "Add to Home Screen"', icon: '➕', detail: 'Find this option in the share menu' },
            { step: 3, text: 'Tap "Add" to confirm', icon: '✅', detail: 'Smriti will be added to your home screen' }
        ] : [
            { step: 1, text: 'Tap the menu button (⋯)', icon: '⋯', detail: 'Look for three dots in the browser' },
            { step: 2, text: 'Tap "Add to Home Screen"', icon: '➕', detail: 'Find this option in the menu' },
            { step: 3, text: 'Tap "Add" to confirm', icon: '✅', detail: 'Smriti will be added to your home screen' }
        ];
        
        instructionModal.innerHTML = `
            <div class="ios-instruction-overlay">
                <div class="ios-instruction-content">
                    <div class="ios-instruction-header">
                        <h3>Add Smriti to Home Screen</h3>
                        <button class="ios-instruction-close" id="ios-instructions-close">×</button>
                    </div>
                    <div class="ios-instruction-body">
                        <p class="ios-instruction-subtitle">Follow these steps to install Smriti on your iPhone:</p>
                        <div class="ios-instruction-steps">
                            ${instructionSteps.map(step => `
                                <div class="ios-instruction-step">
                                    <div class="ios-step-number">${step.step}</div>
                                    <div class="ios-step-content">
                                        <div class="ios-step-icon">${step.icon}</div>
                                        <div class="ios-step-text">
                                            <strong>${step.text}</strong>
                                            <small>${step.detail}</small>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        <div class="ios-instruction-footer">
                            <p><strong>Using ${browserName} on iOS?</strong> ${isSafari ? 'These steps work in Safari.' : 'Try opening this page in Safari for easier installation.'}</p>
                        </div>
                    </div>
                    <div class="ios-instruction-actions">
                        <button class="ios-instruction-btn" id="ios-instructions-done">Got it!</button>
                    </div>
                </div>
            </div>
        `;
        
        // Store reference and add event listeners
        this.iosInstructionModal = instructionModal;
        this.setupIOSModalEventListeners();
        
        // Append to document
        document.body.appendChild(instructionModal);
    }
    
    setupModalEventListeners() {
        // Wait for next tick to ensure DOM elements are added
        setTimeout(() => {
            const closeBtn = document.getElementById('pwa-modal-close');
            const cancelBtn = document.getElementById('pwa-modal-cancel');
            const installBtn = document.getElementById('pwa-modal-install');
            
            if (closeBtn) {
                closeBtn.addEventListener('click', () => this.hideInstallModal());
            }
            if (cancelBtn) {
                cancelBtn.addEventListener('click', () => this.dismissPrompt());
            }
            if (installBtn) {
                installBtn.addEventListener('click', () => this.handleModalInstallClick());
            }
            
            // Close modal when clicking overlay
            if (this.installModal) {
                this.installModal.addEventListener('click', (e) => {
                    if (e.target === this.installModal || e.target.classList.contains('install-modal-overlay')) {
                        this.hideInstallModal();
                    }
                });
            }
        }, 0);
    }
    
    setupIOSModalEventListeners() {
        if (!this.iosInstructionModal) return;
        
        // Wait for next tick to ensure DOM elements are added
        setTimeout(() => {
            const closeBtn = document.getElementById('ios-instructions-close');
            const doneBtn = document.getElementById('ios-instructions-done');
            
            if (closeBtn) {
                closeBtn.addEventListener('click', () => this.hideIOSInstructions());
            }
            if (doneBtn) {
                doneBtn.addEventListener('click', () => this.hideIOSInstructions());
            }
            
            // Close modal when clicking overlay
            if (this.iosInstructionModal) {
                this.iosInstructionModal.addEventListener('click', (e) => {
                    if (e.target === this.iosInstructionModal || e.target.classList.contains('ios-instruction-overlay')) {
                        this.hideIOSInstructions();
                    }
                });
            }
        }, 0);
    }
    
    addModalStyles() {
        const style = document.createElement('style');
        style.textContent = `
            /* Main Install Modal Styles */
            .pwa-install-modal {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 10000;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            .install-modal-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                box-sizing: border-box;
            }
            
            .install-modal-content {
                background: white;
                border-radius: 16px;
                max-width: 380px;
                width: 100%;
                max-height: 90vh;
                overflow-y: auto;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                animation: modalSlideUp 0.3s ease-out;
            }
            
            @keyframes modalSlideUp {
                from {
                    transform: translateY(50px);
                    opacity: 0;
                }
                to {
                    transform: translateY(0);
                    opacity: 1;
                }
            }
            
            .install-modal-header {
                display: flex;
                align-items: center;
                padding: 20px 20px 16px;
                border-bottom: 1px solid #f0f0f0;
                position: relative;
            }
            
            .install-app-icon {
                width: 48px;
                height: 48px;
                border-radius: 12px;
                margin-right: 12px;
                flex-shrink: 0;
            }
            
            .install-app-info {
                flex: 1;
                min-width: 0;
            }
            
            .install-app-name {
                margin: 0 0 4px 0;
                font-size: 18px;
                font-weight: 600;
                color: #1a1a1a;
            }
            
            .install-app-url {
                margin: 0;
                font-size: 14px;
                color: #666;
            }
            
            .install-close-btn {
                position: absolute;
                top: 16px;
                right: 16px;
                background: none;
                border: none;
                font-size: 24px;
                color: #666;
                cursor: pointer;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                transition: background 0.2s ease;
            }
            
            .install-close-btn:hover {
                background: #f0f0f0;
            }
            
            .install-modal-body {
                padding: 20px;
            }
            
            .install-description {
                margin: 0 0 20px 0;
                font-size: 16px;
                line-height: 1.4;
                color: #333;
            }
            
            .install-features {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .install-feature {
                display: flex;
                align-items: center;
                gap: 12px;
                font-size: 14px;
                color: #555;
            }
            
            .install-feature-icon {
                font-size: 18px;
                width: 24px;
                text-align: center;
            }
            
            .install-modal-actions {
                padding: 16px 20px 20px;
                display: flex;
                gap: 12px;
                justify-content: flex-end;
            }
            
            .install-btn-cancel {
                background: none;
                border: 1px solid #ddd;
                color: #666;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .install-btn-cancel:hover {
                background: #f5f5f5;
                border-color: #ccc;
            }
            
            .install-btn-primary {
                background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
                border: none;
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                min-width: 120px;
            }
            
            .install-btn-primary:hover {
                background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(243, 156, 18, 0.3);
            }
            
            /* iOS Instructions Modal */
            .pwa-ios-instructions {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 10001;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            
            .ios-instruction-overlay {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.6);
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
                box-sizing: border-box;
            }
            
            .ios-instruction-content {
                background: white;
                border-radius: 16px;
                max-width: 420px;
                width: 100%;
                max-height: 90vh;
                overflow-y: auto;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                animation: modalSlideUp 0.3s ease-out;
            }
            
            .ios-instruction-header {
                padding: 20px 20px 16px;
                border-bottom: 1px solid #f0f0f0;
                position: relative;
                text-align: center;
            }
            
            .ios-instruction-header h3 {
                margin: 0;
                font-size: 18px;
                font-weight: 600;
                color: #1a1a1a;
            }
            
            .ios-instruction-close {
                position: absolute;
                top: 16px;
                right: 16px;
                background: none;
                border: none;
                font-size: 24px;
                color: #666;
                cursor: pointer;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                transition: background 0.2s ease;
            }
            
            .ios-instruction-close:hover {
                background: #f0f0f0;
            }
            
            .ios-instruction-body {
                padding: 20px;
            }
            
            .ios-instruction-subtitle {
                margin: 0 0 24px 0;
                font-size: 16px;
                color: #666;
                text-align: center;
            }
            
            .ios-instruction-steps {
                display: flex;
                flex-direction: column;
                gap: 20px;
                margin-bottom: 24px;
            }
            
            .ios-instruction-step {
                display: flex;
                align-items: flex-start;
                gap: 16px;
            }
            
            .ios-step-number {
                width: 24px;
                height: 24px;
                background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
                color: white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: 600;
                flex-shrink: 0;
                margin-top: 4px;
            }
            
            .ios-step-content {
                display: flex;
                align-items: flex-start;
                gap: 12px;
                flex: 1;
            }
            
            .ios-step-icon {
                font-size: 24px;
                flex-shrink: 0;
                margin-top: 2px;
            }
            
            .ios-step-text {
                flex: 1;
            }
            
            .ios-step-text strong {
                display: block;
                font-size: 16px;
                color: #1a1a1a;
                margin-bottom: 4px;
            }
            
            .ios-step-text small {
                font-size: 14px;
                color: #666;
                line-height: 1.3;
            }
            
            .ios-instruction-footer {
                background: #f8f9fa;
                padding: 16px;
                border-radius: 8px;
                margin-top: 16px;
            }
            
            .ios-instruction-footer p {
                margin: 0;
                font-size: 14px;
                color: #666;
                text-align: center;
            }
            
            .ios-instruction-actions {
                padding: 16px 20px 20px;
                text-align: center;
            }
            
            .ios-instruction-btn {
                background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
                border: none;
                color: white;
                padding: 12px 32px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
            }
            
            .ios-instruction-btn:hover {
                background: linear-gradient(135deg, #e67e22 0%, #d35400 100%);
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(243, 156, 18, 0.3);
            }
            
            /* Legacy banner styles (fallback) */
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
        
        // Append styles to document
        document.head.appendChild(style);
    }
    
    showInstallPrompt() {
        if (this.isInstalled || this.promptShown) {
            return;
        }
        
        console.log('Showing install prompt for platform:', this.platform);
        
        if (this.installModal) {
            this.installModal.style.display = 'block';
            this.promptShown = true;
            
            // Track in analytics if available
            if (window.gtag) {
                gtag('event', 'pwa_prompt_shown', {
                    event_category: 'PWA',
                    event_label: `Install Prompt Shown - ${this.platform.isIOS ? 'iOS' : 'Android'}`,
                    platform: this.platform.isIOS ? 'iOS' : 'Android',
                    browser: this.platform.browserName
                });
            }
        }
    }
    
    hideInstallModal() {
        if (this.installModal) {
            this.installModal.style.display = 'none';
        }
    }
    
    showIOSInstructions() {
        if (this.iosInstructionModal) {
            this.iosInstructionModal.style.display = 'block';
            
            // Track iOS instruction view
            if (window.gtag) {
                gtag('event', 'ios_instructions_shown', {
                    event_category: 'PWA',
                    event_label: 'iOS Install Instructions Shown',
                    browser: this.platform.browserName
                });
            }
        }
    }
    
    hideIOSInstructions() {
        if (this.iosInstructionModal) {
            this.iosInstructionModal.style.display = 'none';
        }
    }
    
    handleModalInstallClick() {
        if (this.platform.isIOS) {
            // For iOS, hide main modal and show instructions
            this.hideInstallModal();
            this.showIOSInstructions();
        } else {
            // For Android/Chrome, trigger native install
            this.handleAndroidInstall();
        }
    }
    
    async handleAndroidInstall() {
        if (!this.deferredPrompt) {
            console.log('No deferred prompt available, showing manual instructions');
            this.hideInstallModal();
            this.showManualInstallInstructions();
            return;
        }
        
        try {
            console.log('Triggering Android install prompt');
            
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
                    value: outcome === 'accepted' ? 1 : 0,
                    platform: 'Android'
                });
            }
            
            if (outcome === 'accepted') {
                console.log('User accepted the Android install prompt');
                this.hideInstallModal();
            } else {
                console.log('User dismissed the Android install prompt');
                this.dismissPrompt();
            }
            
            // Clear the saved prompt
            this.deferredPrompt = null;
            
        } catch (error) {
            console.error('Error during Android install:', error);
            this.hideInstallModal();
            this.showManualInstallInstructions();
        }
    }
    
    async handleInstallClick() {
        // Legacy method for compatibility
        this.handleModalInstallClick();
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
        // Hide both modals
        this.hideInstallModal();
        this.hideIOSInstructions();
        
        // Hide legacy banner if exists
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
                event_label: 'Install Prompt Dismissed',
                platform: this.platform.isIOS ? 'iOS' : 'Android',
                browser: this.platform.browserName
            });
        }
    }
    
    handleAppInstalled() {
        this.isInstalled = true;
        
        // Hide all modals and banners
        this.hideInstallModal();
        this.hideIOSInstructions();
        if (this.installBanner) {
            this.installBanner.style.display = 'none';
        }
        
        // Clear dismissal flags
        localStorage.removeItem('pwa-install-dismissed');
        localStorage.removeItem('pwa-install-dismissed-time');
        
        // Show success message
        this.showInstallToast('Smriti installed successfully!');
        
        // Track installation
        if (window.gtag) {
            gtag('event', 'pwa_installed', {
                event_category: 'PWA',
                event_label: 'App Installed Successfully',
                platform: this.platform.isIOS ? 'iOS' : 'Android',
                browser: this.platform.browserName
            });
        }
    }
    
    addIOSTestButton() {
        // Add a temporary test button for iOS debugging
        const testButton = document.createElement('button');
        testButton.textContent = 'Test iOS Install Popup';
        testButton.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 10002;
            background: #f39c12;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
        `;
        testButton.addEventListener('click', () => {
            console.log('Test button clicked - forcing iOS popup');
            this.promptShown = false; // Reset to allow showing
            this.showInstallPrompt();
        });
        document.body.appendChild(testButton);
        
        // Auto-remove after 30 seconds
        setTimeout(() => {
            if (testButton.parentNode) {
                testButton.remove();
            }
        }, 30000);
    }
}

// Initialize when script loads
window.pwaInstallManager = new PWAInstallManager();