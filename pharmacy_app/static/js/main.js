/**
 * Main JavaScript file for Pharmacy Management System
 * Handles general UI functionality and initializations
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all Materialize components
    initializeMaterialize();
    
    // Set up notifications
    setupNotifications();
    
    // Handle message auto-dismissal
    setupMessageDismissal();
    
    // Initialize custom form validations
    setupFormValidations();
    
    // Navbar active state
    setActiveNavLink();
});

/**
 * Initialize all Materialize CSS components
 */
function initializeMaterialize() {
    // Navigation components
    const sideNav = document.querySelectorAll('.sidenav');
    M.Sidenav.init(sideNav);
    
    const dropdowns = document.querySelectorAll('.dropdown-trigger');
    M.Dropdown.init(dropdowns, {
        constrainWidth: false,
        coverTrigger: false
    });
    
    // Form components
    const selects = document.querySelectorAll('select');
    M.FormSelect.init(selects);
    
    const datepickers = document.querySelectorAll('.datepicker');
    M.Datepicker.init(datepickers, {
        format: 'yyyy-mm-dd',
        autoClose: true
    });
    
    // Interactive components
    const tooltips = document.querySelectorAll('.tooltipped');
    M.Tooltip.init(tooltips);
    
    const modals = document.querySelectorAll('.modal');
    M.Modal.init(modals);
    
    const tabs = document.querySelectorAll('.tabs');
    M.Tabs.init(tabs);
    
    const collapsibles = document.querySelectorAll('.collapsible');
    M.Collapsible.init(collapsibles);
}

/**
 * Set up notification functionality
 */
function setupNotifications() {
    // Notification counter handler
    const notificationTrigger = document.getElementById('notification-trigger');
    const notificationBadge = document.querySelector('.badge-notify');
    
    if (notificationTrigger && notificationBadge) {
        const count = parseInt(notificationBadge.textContent);
        
        if (count > 0) {
            notificationTrigger.classList.add('pulse');
        }
    }
}

/**
 * Setup auto-dismissal for flash messages
 */
function setupMessageDismissal() {
    const messages = document.querySelectorAll('.card-panel:has(span.red-text, span.green-text, span.orange-text, span.blue-text)');
    
    if (messages.length > 0) {
        setTimeout(function() {
            messages.forEach(msg => {
                fadeOut(msg);
            });
        }, 5000);
    }
}

/**
 * Helper function to fade out elements
 */
function fadeOut(element) {
    let opacity = 1;
    const timer = setInterval(function() {
        if (opacity <= 0.1) {
            clearInterval(timer);
            element.style.display = 'none';
        }
        element.style.opacity = opacity;
        opacity -= 0.1;
    }, 50);
}

/**
 * Setup custom form validations beyond what Django provides
 */
function setupFormValidations() {
    // Add validation for numeric fields
    const numericInputs = document.querySelectorAll('input[type="number"]');
    
    numericInputs.forEach(input => {
        input.addEventListener('input', function() {
            // Remove non-numeric characters except decimal point
            this.value = this.value.replace(/[^0-9.]/g, '');
            
            // Ensure only one decimal point
            const decimalCount = (this.value.match(/\./g) || []).length;
            if (decimalCount > 1) {
                this.value = this.value.slice(0, -1);
            }
        });
    });
    
    // Date validation for expiry dates
    const expiryDateInputs = document.querySelectorAll('input[id*="expiry_date"]');
    
    expiryDateInputs.forEach(input => {
        input.addEventListener('change', function() {
            const selectedDate = new Date(this.value);
            const today = new Date();
            
            if (selectedDate < today) {
                M.toast({html: 'Warning: The selected date is in the past!', classes: 'warning'});
                this.classList.add('invalid');
            } else {
                this.classList.remove('invalid');
            }
        });
    });
}

/**
 * Set active state on navigation links based on current URL
 */
function setActiveNavLink() {
    const currentPath = window.location.pathname;
    
    // Find nav links that match the current path
    const navLinks = document.querySelectorAll('.sidenav a, .nav-wrapper a');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        
        // Skip dropdown triggers and non-links
        if (!href || link.classList.contains('dropdown-trigger') || href === '#') return;
        
        // Check if the current path starts with the link's href
        if (currentPath === href || 
            (href !== '/' && currentPath.startsWith(href))) {
            link.classList.add('active');
            
            // If it's in the sidenav, add active class to parent li
            const parentLi = link.closest('li');
            if (parentLi) {
                parentLi.classList.add('active');
            }
        }
    });
}

/**
 * Format currency display
 * @param {number} value - The numeric value to format
 * @returns {string} - Formatted currency string
 */
function formatCurrency(value) {
    return parseFloat(value).toFixed(0) + ' IQD';
}

/**
 * Format date in user-friendly format
 * @param {string} dateString - ISO date string
 * @returns {string} - Formatted date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Show a custom confirmation dialog
 * @param {string} message - The confirmation message
 * @param {function} onConfirm - Callback function when confirmed
 */
function confirmAction(message, onConfirm) {
    if (confirm(message)) {
        onConfirm();
    }
}

/**
 * Initialize dynamically added form elements
 * Called after adding form elements via JavaScript
 */
function initFormElements() {
    const selects = document.querySelectorAll('select');
    M.FormSelect.init(selects);
    
    const datepickers = document.querySelectorAll('.datepicker');
    M.Datepicker.init(datepickers, {
        format: 'yyyy-mm-dd',
        autoClose: true
    });
    
    const tooltips = document.querySelectorAll('.tooltipped');
    M.Tooltip.init(tooltips);
    
    // If we're on the sales page and there's a sales.js script, 
    // the drug selects will be converted to autocomplete there
}
