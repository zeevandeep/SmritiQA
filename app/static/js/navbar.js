/**
 * Hamburger Menu Click-Outside-to-Close Functionality
 * 
 * This script adds click-outside behavior to the hamburger menu.
 * When the menu is open, clicking anywhere outside the menu or hamburger button
 * will close the menu. Menu links continue to work as expected.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Get navbar elements
    const navbarMenu = document.getElementById('navbarMenu');
    const navbarToggler = document.querySelector('.navbar-toggler');
    
    // Only proceed if both elements exist
    if (!navbarMenu || !navbarToggler) {
        console.warn('Navbar elements not found - click-outside functionality disabled');
        return;
    }
    
    // Add click event listener to document
    document.addEventListener('click', function(event) {
        // Only proceed if menu is currently open
        if (!navbarMenu.classList.contains('show')) {
            return;
        }
        
        // Check if click was outside both the menu and the hamburger button
        const clickedInsideMenu = navbarMenu.contains(event.target);
        const clickedHamburgerButton = navbarToggler.contains(event.target);
        
        // Close menu if clicked outside both elements
        if (!clickedInsideMenu && !clickedHamburgerButton) {
            navbarMenu.classList.remove('show');
        }
    });
    
    // Optional: Close menu when clicking on navigation links (maintains current behavior)
    const menuLinks = navbarMenu.querySelectorAll('.nav-link');
    menuLinks.forEach(function(link) {
        link.addEventListener('click', function() {
            navbarMenu.classList.remove('show');
        });
    });
});