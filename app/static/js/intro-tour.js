// Smriti Onboarding Tour using Intro.js
// This tour guides new users through the key features of the app

class SmritiTour {
    constructor() {
        this.introInstance = null;
    }

    // Check if user has seen the tour before (from database)
    async hasSeenTour() {
        try {
            const user = await this.getCurrentUser();
            if (!user || !user.id) return true; // If no user, don't show tour
            
            const response = await fetch(`/api/v1/tour/status/${user.id}`, {
                headers: { 'Authorization': `Bearer ${this.getAccessToken()}` }
            });
            
            if (response.ok) {
                const data = await response.json();
                return data.tour_completed;
            }
            return true; // If API fails, assume tour completed to avoid showing
        } catch (error) {
            console.error('Error checking tour status:', error);
            return true; // If error, assume tour completed to avoid showing
        }
    }

    // Get current user (helper method)
    async getCurrentUser() {
        try {
            const response = await fetch('/api/v1/users/me', {
                headers: { 'Authorization': `Bearer ${this.getAccessToken()}` }
            });
            if (response.ok) {
                return await response.json();
            }
            return null;
        } catch (error) {
            console.error('Error getting current user:', error);
            return null;
        }
    }

    // Get access token from cookies
    getAccessToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'smriti_access_token') {
                return value;
            }
        }
        return null;
    }

    // Initialize the tour for new users
    async init() {
        // Check URL parameters for tour triggers
        const urlParams = new URLSearchParams(window.location.search);
        const isWelcome = urlParams.get('welcome') === 'true';
        const isTourStart = urlParams.get('tour') === 'start';
        
        // Check if user has seen tour before
        const hasSeenTour = await this.hasSeenTour();
        
        // Show tour if user hasn't seen it before OR if explicitly requested
        if (!hasSeenTour || isWelcome || isTourStart) {
            // Small delay to ensure page is fully loaded
            setTimeout(() => {
                this.startTour();
            }, 1000);
        }
    }

    // Start the onboarding tour
    startTour() {
        // Import Intro.js dynamically if not already loaded
        if (typeof introJs === 'undefined') {
            this.loadIntroJS(() => {
                this.configureTour();
            });
        } else {
            this.configureTour();
        }
    }

    // Load Intro.js library dynamically
    loadIntroJS(callback) {
        // Load CSS
        const css = document.createElement('link');
        css.rel = 'stylesheet';
        css.href = 'https://cdn.jsdelivr.net/npm/intro.js@7.2.0/introjs.min.css';
        document.head.appendChild(css);

        // Load JS
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/intro.js@7.2.0/intro.min.js';
        script.onload = callback;
        document.head.appendChild(script);
    }

    // Configure and start the actual tour
    configureTour() {
        this.introInstance = introJs();
        
        // Custom styling for Smriti's orange theme
        const customCSS = `
            <style id="smriti-tour-styles">
                .introjs-tooltip {
                    max-width: 420px;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                    border: none;
                }
                .introjs-tooltipbuttons {
                    padding: 12px 20px 16px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 10px;
                }
                .introjs-nextbutton {
                    margin-left: auto;
                }
                .introjs-prevbutton {
                    margin-right: auto;
                }
                .introjs-tooltip-header {
                    background: linear-gradient(135deg, #f39c12, #e67e22);
                    color: white;
                    padding: 14px 20px;
                    border-radius: 12px 12px 0 0;
                    font-weight: 600;
                }
                .introjs-tooltip-title {
                    color: white;
                    font-size: 18px;
                    margin: 0;
                }
                .introjs-tooltiptext {
                    padding: 18px 20px;
                    line-height: 1.5;
                    font-size: 15px;
                }
                .introjs-button {
                    background: transparent !important;
                    color: #f39c12;
                    border: none !important;
                    padding: 8px 12px;
                    border-radius: 0 !important;
                    font-weight: 500;
                    font-size: 24px;
                    white-space: nowrap;
                    transition: all 0.2s;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-width: 44px;
                    height: 36px;
                    cursor: pointer;
                    outline: none !important;
                    box-shadow: none !important;
                }
                .introjs-button:hover {
                    background: transparent !important;
                    color: #e67e22;
                    transform: scale(1.1);
                }
                .introjs-skipbutton {
                    color: #6c757d;
                    background: transparent;
                    border: 1px solid #dee2e6;
                    font-size: 13px;
                    font-weight: 400;
                    white-space: nowrap;
                    padding: 8px 14px;
                    min-width: 80px;
                    height: 36px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .introjs-skipbutton:hover {
                    background: #f8f9fa;
                }
                .introjs-overlay {
                    background: rgba(0,0,0,0.4);
                }
                .introjs-helperLayer {
                    border-radius: 8px;
                    box-shadow: 0 0 0 9999px rgba(0,0,0,0.4);
                }
                .introjs-tooltip[data-step="0"] .introjs-prevbutton {
                    color: #ccc !important;
                    pointer-events: none !important;
                    opacity: 0.4 !important;
                }
                .introjs-tooltip[data-step="0"] .introjs-tooltipbuttons {
                    justify-content: space-between !important;
                }
                .introjs-tooltip[data-step="6"] .introjs-donebutton {
                    color: #ccc !important;
                    pointer-events: none !important;
                    opacity: 0.4 !important;
                }
            </style>
        `;
        document.head.insertAdjacentHTML('beforeend', customCSS);

        const steps = this.getTourSteps();

        this.introInstance.setOptions({
            steps: steps,
            showStepNumbers: false,
            showBullets: false,
            exitOnOverlayClick: false,
            exitOnEsc: true,
            nextLabel: '▶',
            prevLabel: '◀',
            skipLabel: 'Skip',
            doneLabel: '▶',
            tooltipClass: 'smriti-tooltip',
            highlightClass: 'smriti-highlight',
            overlayOpacity: 0.4
        });

        // Event handlers
        this.introInstance.onbeforechange((targetElement) => {
            // Ensure elements are visible before highlighting
            this.prepareStepElement(targetElement);
            
            // Hide back button on first step
            setTimeout(() => {
                const currentStep = this.introInstance._currentStep;
                const tooltip = document.querySelector('.introjs-tooltip');
                if (tooltip) {
                    tooltip.setAttribute('data-step', currentStep);
                }
            }, 10);
        });

        this.introInstance.oncomplete(() => {
            this.completeTour();
        });

        this.introInstance.onexit(() => {
            this.skipTour();
        });

        // Start the tour
        this.introInstance.start();
    }

    // Define the tour steps
    getTourSteps() {
        const currentPath = window.location.pathname;
        
        // Base steps that work on journal page
        const baseSteps = [
            {
                intro: `
                    <div style="text-align: center;">
                        <h3 style="color: #ff6b35; margin-bottom: 16px;">Welcome to Smriti!</h3>
                        <p style="margin-bottom: 16px;">Smriti is your AI-powered journaling companion that helps you discover patterns in your thoughts and feelings.</p>
                        <p style="font-size: 14px; color: #6c757d;">This quick tour will show you how to get started. It takes about 1 minute.</p>
                    </div>
                `
            }
        ];

        // Journal page specific steps
        if (currentPath === '/journal' || currentPath === '/') {
            return baseSteps.concat([
                {
                    element: '.bottom-nav a[href="/journal"]',
                    intro: `
                        <p>Use this to record your journal entries. This is where you'll start your daily journaling practice.</p>
                    `,
                    position: 'top'
                },
                {
                    element: '.input-mode-toggle',
                    intro: `
                        <p>You can journal in two ways:</p>
                        <ul style="margin: 12px 0; padding-left: 20px;">
                            <li><strong>Voice:</strong> Tap the microphone and speak your thoughts</li>
                            <li><strong>Text:</strong> Click the pen icon and type your entry</li>
                        </ul>
                    `,
                    position: 'bottom'
                },
                {
                    intro: `
                        <p>After recording or typing, Smriti's AI will:</p>
                        <ul style="margin: 12px 0; padding-left: 20px;">
                            <li><strong>Analyze</strong> your thoughts and emotions</li>
                            <li><strong>Identify</strong> meaningful patterns in your reflections</li>
                            <li><strong>Connect</strong> your current entry to past memories</li>
                        </ul>
                    `
                },
                {
                    element: '.bottom-nav a[href="/entries"]',
                    intro: `
                        <p>Navigate here to view your past journal entries and track your journaling journey over time.</p>
                    `,
                    position: 'top'
                },
                {
                    element: '.bottom-nav a[href="/generate-reflection"]',
                    intro: `
                        <p>Navigate here to generate new reflections from your past journal entries. It takes minimum 4 to 5 journaling entries for Smriti AI to discover meaningful insights.</p>
                    `,
                    position: 'top'
                },
                {
                    element: '.bottom-nav a[href="/reflections"]',
                    intro: `
                        <p>Navigate here to view past reflections and explore the insights Smriti has discovered about your emotional patterns.</p>
                    `,
                    position: 'top'
                }
            ]);
        }

        // Generic steps for other pages
        return baseSteps.concat([
            {
                intro: `
                    <h4>🚀 Ready to Start!</h4>
                    <p>Visit the Journal page to create your first entry. Smriti will:</p>
                    <ul style="margin: 12px 0; padding-left: 20px;">
                        <li>Analyze your thoughts with AI</li>
                        <li>Find patterns in your emotions</li>
                        <li>Generate personalized insights</li>
                        <li>Keep everything encrypted and private</li>
                    </ul>
                    <p style="font-size: 14px; color: #6c757d;">Let's explore your inner world together!</p>
                `
            }
        ]);
    }

    // Prepare elements before each step
    prepareStepElement(targetElement) {
        if (!targetElement) return;

        // Scroll element into view
        targetElement.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
    }

    // Handle tour completion
    // Complete tour and mark in database
    async completeTour() {
        try {
            const user = await this.getCurrentUser();
            if (user && user.id) {
                await fetch(`/api/v1/tour/complete/${user.id}`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${this.getAccessToken()}` }
                });
            }
        } catch (error) {
            console.error('Error marking tour as completed:', error);
        }
        this.removeTourStyles();
    }

    // Handle tour skip and mark in database
    async skipTour() {
        try {
            const user = await this.getCurrentUser();
            if (user && user.id) {
                await fetch(`/api/v1/tour/complete/${user.id}`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${this.getAccessToken()}` }
                });
            }
        } catch (error) {
            console.error('Error marking tour as completed:', error);
        }
        this.removeTourStyles();
    }

    // Remove custom tour styles
    removeTourStyles() {
        const styles = document.getElementById('smriti-tour-styles');
        if (styles) {
            styles.remove();
        }
    }

    // Show a nice completion message
    showCompletionMessage() {
        const message = document.createElement('div');
        message.innerHTML = `
            <div style="
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                text-align: center;
                z-index: 10000;
                max-width: 400px;
                border: 2px solid #ff6b35;
            ">
                <h3 style="color: #ff6b35; margin-bottom: 16px;">Welcome Aboard! 🎉</h3>
                <p style="margin-bottom: 20px;">You're all set to start your emotional journaling journey with Smriti.</p>
                <button onclick="this.parentElement.parentElement.remove()" style="
                    background: #ff6b35;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: 500;
                    cursor: pointer;
                ">Start Journaling</button>
            </div>
            <div style="
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.4);
                z-index: 9999;
            " onclick="this.parentElement.remove()"></div>
        `;
        document.body.appendChild(message);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (message.parentElement) {
                message.remove();
            }
        }, 5000);
    }

    // Manual tour trigger (for settings or help)
    // Manual tour start (for "How to Use" page)
    manualStart() {
        // No need to remove anything from database - just start the tour
        this.startTour();
    }

    // Reset tour for testing
    resetTour() {
        localStorage.removeItem('smriti_tour_completed');
        this.hasSeenTour = false;
    }
}

// Initialize tour when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.smritiTour = new SmritiTour();
    
    // Auto-start for new users
    window.smritiTour.init();
});

// Export for global access
window.SmritiTour = SmritiTour;