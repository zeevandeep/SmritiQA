/**
 * Hamburger Menu Click-Outside-to-Close Functionality
 * 
 * This script adds click-outside behavior to the hamburger menu using Bootstrap's
 * official Collapse API to ensure consistent smooth animations.
 */

document.addEventListener('DOMContentLoaded', () => {
    const navbarMenu = document.getElementById('navbarMenu');  // This is your collapsible menu
    const navbarToggler = document.querySelector('.navbar-toggler'); // The hamburger button

    if (!navbarMenu || !navbarToggler) {
        console.warn('Navbar elements not found - click-outside functionality disabled');
        return;
    }

    document.addEventListener('click', (event) => {
        const isMenuOpen = navbarMenu.classList.contains('show');
        const clickedInsideMenu = navbarMenu.contains(event.target);
        const clickedToggler = navbarToggler.contains(event.target);

        // Only collapse if menu is open and the click was outside both the menu and the hamburger
        if (isMenuOpen && !clickedInsideMenu && !clickedToggler) {
            const collapseInstance = bootstrap.Collapse.getInstance(navbarMenu);

            if (collapseInstance) {
                collapseInstance.hide();  // ✅ Triggers smooth Bootstrap collapse animation
            } else {
                // Optional: fallback if Collapse instance not initialized (shouldn't happen if Bootstrap JS loaded)
                navbarMenu.classList.remove('show');
            }
        }
    });

    // Close menu when clicking on navigation links (maintains current behavior)
    const menuLinks = navbarMenu.querySelectorAll('.nav-link');
    menuLinks.forEach(function(link) {
        link.addEventListener('click', function() {
            const collapseInstance = bootstrap.Collapse.getInstance(navbarMenu);
            if (collapseInstance) {
                collapseInstance.hide();  // Use Bootstrap API for consistent animation
            } else {
                navbarMenu.classList.remove('show');
            }
        });
    });
});