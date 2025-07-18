// Smriti Onboarding Tour using Intro.js
// This tour guides new users through the key features of the app

class SmritiTour {
    constructor() {
        this.hasSeenTour = localStorage.getItem('smriti_tour_completed');
        this.introInstance = null;
    }

    // Initialize the tour for new users
    init() {
        // Check URL parameters for tour triggers
        const urlParams = new URLSearchParams(window.location.search);
        const isWelcome = urlParams.get('welcome') === 'true';
        const isTourStart = urlParams.get('tour') === 'start';
        
        // Show tour if user hasn't seen it before OR if explicitly requested
        if (!this.hasSeenTour || isWelcome || isTourStart) {
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
                    max-width: 350px;
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
                    background: #f39c12;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 6px;
                    font-weight: 500;
                    font-size: 14px;
                    white-space: nowrap;
                    transition: all 0.2s;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    height: 36px;
                }
                .introjs-button:hover {
                    background: #e67e22;
                    transform: translateY(-1px);
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
                
                /* Force center positioning only for AI Processing step */
                .introjs-tooltip[data-step-number="4"] {
                    position: fixed !important;
                    top: 50% !important;
                    left: 50% !important;
                    transform: translate(-50%, -50%) !important;
                    margin: 0 !important;
                }
                
                /* Smooth transition for all tooltips */
                .introjs-tooltip {
                    transition: all 0.1s ease-out;
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
            nextLabel: 'Next →',
            prevLabel: '← Back',
            skipLabel: 'Skip',
            doneLabel: 'Start Exploring! 🎉',
            tooltipClass: 'smriti-tooltip',
            highlightClass: 'smriti-highlight',
            overlayOpacity: 0.4
        });

        // Event handlers
        this.introInstance.onbeforechange((targetElement) => {
            console.log('Step change detected. Current step index:', this.introInstance._currentStep);
            console.log('Target element:', targetElement);
            // Ensure elements are visible before highlighting
            this.prepareStepElement(targetElement);
            
            // Custom positioning for microphone button to avoid covering it
            if (targetElement && targetElement.id === 'micButton') {
                setTimeout(() => {
                    const tooltip = document.querySelector('.introjs-tooltip');
                    if (tooltip) {
                        tooltip.style.transform = 'translateY(-40px) translateX(-50px)';
                        tooltip.style.marginTop = '0px';
                    }
                }, 100);
            }
            
            // Custom positioning for bottom navigation to keep it compact
            if (targetElement && targetElement.classList && targetElement.classList.contains('bottom-nav')) {
                setTimeout(() => {
                    const tooltip = document.querySelector('.introjs-tooltip');
                    if (tooltip) {
                        tooltip.style.transform = 'translateY(-20px)';
                        tooltip.style.maxWidth = '280px';
                    }
                }, 100);
            }
            


        });

        this.introInstance.onafterchange((targetElement) => {
            console.log('Step change detected. Current step index:', this.introInstance._currentStep);
            console.log('Target element:', targetElement);
            
            // Handle positioning for different steps
            const currentStep = this.introInstance._currentStep;
            
            // AI Processing step (step 4) - force center positioning
            if (targetElement && targetElement.id === 'tour-center-point' && currentStep === 4) {
                console.log(`Setting up persistent center positioning for AI Processing step ${currentStep}`);
                
                const forceCenterPosition = () => {
                    const tooltip = document.querySelector('.introjs-tooltip');
                    if (tooltip) {
                        tooltip.style.cssText = `
                            position: fixed !important;
                            top: 50% !important;
                            left: 50% !important;
                            transform: translate(-50%, -50%) !important;
                            margin: 0 !important;
                            z-index: 9999999 !important;
                        `;
                    }
                };
                
                // Apply immediately and with multiple retries
                forceCenterPosition();
                setTimeout(forceCenterPosition, 1);
                setTimeout(forceCenterPosition, 10);
                setTimeout(forceCenterPosition, 50);
                setTimeout(forceCenterPosition, 100);
                setTimeout(forceCenterPosition, 200);
                
                // Set up continuous monitoring only for AI Processing
                this.centeringInterval = setInterval(forceCenterPosition, 100);
            } 
            // Text Journaling step (step 3) - ensure proper positioning above text area
            else if (targetElement && targetElement.id === 'textInputArea' && currentStep === 3) {
                console.log(`Ensuring proper positioning for Text Journaling step ${currentStep}`);
                
                // Make sure text mode is active and text area is visible
                setTimeout(() => {
                    const textModeBtn = document.getElementById('textModeBtn');
                    const textInputArea = document.getElementById('textInputArea');
                    
                    if (textModeBtn && !textModeBtn.classList.contains('active')) {
                        textModeBtn.click(); // Switch to text mode if not already active
                    }
                    
                    // Force proper positioning above text area
                    const tooltip = document.querySelector('.introjs-tooltip');
                    if (tooltip && textInputArea) {
                        const rect = textInputArea.getBoundingClientRect();
                        tooltip.style.cssText = `
                            position: fixed !important;
                            top: ${rect.top - tooltip.offsetHeight - 20}px !important;
                            left: ${rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2)}px !important;
                            transform: none !important;
                            margin: 0 !important;
                            z-index: 9999999 !important;
                        `;
                    }
                }, 50);
            } else {
                // Clear interval when leaving special positioning steps
                if (this.centeringInterval) {
                    clearInterval(this.centeringInterval);
                    this.centeringInterval = null;
                }
            }
        });

        this.introInstance.oncomplete(() => {
            // Clear centering interval if active
            if (this.centeringInterval) {
                clearInterval(this.centeringInterval);
                this.centeringInterval = null;
            }
            this.completeTour();
        });

        this.introInstance.onexit(() => {
            // Clear centering interval if active
            if (this.centeringInterval) {
                clearInterval(this.centeringInterval);
                this.centeringInterval = null;
            }
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
                    element: '.input-mode-toggle',
                    intro: `
                        <h4>📝 Choose Your Input Method</h4>
                        <p>You can journal in two ways:</p>
                        <ul style="margin: 12px 0; padding-left: 20px;">
                            <li><strong>Voice:</strong> Tap the microphone and speak your thoughts</li>
                            <li><strong>Text:</strong> Click the pen icon and type your entry</li>
                        </ul>
                        <p style="font-size: 14px; color: #6c757d;">Try switching between them!</p>
                    `,
                    position: 'bottom'
                },
                {
                    element: '#micButton',
                    intro: `
                        <h4>🎤 Voice Journaling</h4>
                        <p>Tap the microphone to record your thoughts. Supports multiple languages with automatic transcription.</p>
                    `,
                    position: 'top'
                },
                {
                    element: '#textInputArea',
                    intro: `
                        <h4>✍️ Text Journaling</h4>
                        <p>Click the pen icon above to switch to text mode. You can type your thoughts here and use Enter for line breaks.</p>
                        <p style="font-size: 14px; color: #6c757d;">Great for detailed reflection or when you prefer writing!</p>
                    `,
                    position: 'top'
                },
                {
                    element: '#tour-center-point',
                    intro: `
                        <h4>⚡ AI Processing</h4>
                        <p>After recording or typing, Smriti's AI will:</p>
                        <ul style="margin: 12px 0; padding-left: 20px;">
                            <li><strong>Analyze</strong> your thoughts and emotions (~2.4s)</li>
                            <li><strong>Generate embeddings</strong> for pattern recognition (~1.6s)</li>
                            <li><strong>Create connections</strong> to your past entries (~1.5s)</li>
                        </ul>
                        <p style="font-size: 14px; color: #6c757d;">You'll see real-time progress indicators during processing!</p>
                    `
                },
                {
                    element: '.bottom-nav',
                    intro: `
                        <h4>🧭 Navigation</h4>
                        <p>Use the bottom tabs to explore different sections of Smriti.</p>
                        <p style="font-size: 14px; color: #6c757d;">You're ready to start journaling!</p>
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

        // Ensure text input area is visible if it's the target
        if (targetElement.id === 'textInputArea') {
            // Switch to text mode temporarily
            const textToggle = document.getElementById('textToggle');
            if (textToggle && !textToggle.classList.contains('active')) {
                textToggle.click();
            }
        }

        // Scroll element into view
        targetElement.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
    }

    // Handle tour completion
    completeTour() {
        localStorage.setItem('smriti_tour_completed', 'true');
        this.removeTourStyles();
        
        // Show completion message
        this.showCompletionMessage();
    }

    // Handle tour skip
    skipTour() {
        localStorage.setItem('smriti_tour_completed', 'true');
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
    manualStart() {
        localStorage.removeItem('smriti_tour_completed');
        this.hasSeenTour = false;
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