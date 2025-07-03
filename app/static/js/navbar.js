/**
 * Accessible Hamburger Menu Navigation
 * 
 * This script provides click-outside behavior, keyboard navigation,
 * and proper ARIA state management for screen readers.
 */

document.addEventListener('DOMContentLoaded', () => {
    const navbarMenu = document.getElementById('navbarMenu');
    const navbarToggler = document.querySelector('.navbar-toggler');
    const menuLinks = navbarMenu?.querySelectorAll('.nav-link');

    if (!navbarMenu || !navbarToggler) {
        console.warn('Navbar elements not found - accessibility features disabled');
        return;
    }

    // Accessibility: Update ARIA expanded state
    function updateAriaExpanded(isExpanded) {
        navbarToggler.setAttribute('aria-expanded', isExpanded.toString());
    }

    // Accessibility: Focus management
    function manageFocus(menuOpened) {
        if (menuOpened && menuLinks.length > 0) {
            // Focus first menu item when opened via keyboard
            setTimeout(() => menuLinks[0].focus(), 100);
        } else {
            // Return focus to toggle button when closed
            navbarToggler.focus();
        }
    }

    // Enhanced menu close function with accessibility
    function closeMenu(returnFocus = false) {
        const collapseInstance = bootstrap.Collapse.getInstance(navbarMenu);
        
        if (collapseInstance) {
            collapseInstance.hide();
        } else {
            navbarMenu.classList.remove('show');
            updateAriaExpanded(false);
        }
        
        if (returnFocus) {
            manageFocus(false);
        }
    }

    // Click outside to close menu
    document.addEventListener('click', (event) => {
        const isMenuOpen = navbarMenu.classList.contains('show');
        const clickedInsideMenu = navbarMenu.contains(event.target);
        const clickedToggler = navbarToggler.contains(event.target);

        if (isMenuOpen && !clickedInsideMenu && !clickedToggler) {
            closeMenu();
        }
    });

    // Keyboard navigation support
    document.addEventListener('keydown', (event) => {
        const isMenuOpen = navbarMenu.classList.contains('show');
        
        // ESC key closes menu
        if (event.key === 'Escape' && isMenuOpen) {
            event.preventDefault();
            closeMenu(true);
            return;
        }

        // Arrow key navigation within menu
        if (isMenuOpen && menuLinks.length > 0) {
            const focusedIndex = Array.from(menuLinks).findIndex(link => 
                document.activeElement === link
            );

            if (event.key === 'ArrowDown') {
                event.preventDefault();
                const nextIndex = (focusedIndex + 1) % menuLinks.length;
                menuLinks[nextIndex].focus();
            } else if (event.key === 'ArrowUp') {
                event.preventDefault();
                const prevIndex = focusedIndex <= 0 ? menuLinks.length - 1 : focusedIndex - 1;
                menuLinks[prevIndex].focus();
            } else if (event.key === 'Home') {
                event.preventDefault();
                menuLinks[0].focus();
            } else if (event.key === 'End') {
                event.preventDefault();
                menuLinks[menuLinks.length - 1].focus();
            }
        }
    });

    // Close menu when clicking navigation links
    menuLinks.forEach(function(link) {
        link.addEventListener('click', function() {
            closeMenu();
        });

        // Accessibility: Enhanced keyboard support for menu items
        link.addEventListener('keydown', function(event) {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                link.click();
            }
        });
    });

    // Listen for Bootstrap collapse events to update ARIA states
    navbarMenu.addEventListener('show.bs.collapse', () => {
        updateAriaExpanded(true);
    });

    navbarMenu.addEventListener('hide.bs.collapse', () => {
        updateAriaExpanded(false);
    });

    navbarMenu.addEventListener('shown.bs.collapse', () => {
        // Focus management after menu is fully opened
        if (document.activeElement === navbarToggler) {
            manageFocus(true);
        }
    });
});