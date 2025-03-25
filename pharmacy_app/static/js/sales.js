/**
 * Sales module for Pharmacy Management System
 * Handles the sales form, including dynamic addition/removal of items,
 * price calculations, and drug interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeSalesForm();
});

/**
 * Initialize the sales form
 */
function initializeSalesForm() {
    // Set up form handlers
    setupFormsetManagement();
    setupItemPriceCalculation();
    setupTotalCalculation();
    
    // Initialize select fields
    initializeSelectFields();
    
    // Set up form validation
    setupFormValidation();
}

/**
 * Set up formset management (add/remove items)
 */
function setupFormsetManagement() {
    const addButton = document.getElementById('add-more');
    const totalForms = document.getElementById('id_saleitems-TOTAL_FORMS');
    const formContainer = document.getElementById('sale-items');
    
    if (!addButton || !totalForms || !formContainer) return;
    
    // Add item button click handler
    addButton.addEventListener('click', function(e) {
        e.preventDefault();
        
        const formCount = parseInt(totalForms.value);
        const emptyFormHtml = document.getElementById('empty-form').innerHTML;
        const newFormHtml = emptyFormHtml.replace(/__prefix__/g, formCount);
        
        formContainer.insertAdjacentHTML('beforeend', newFormHtml);
        totalForms.value = formCount + 1;
        
        // Initialize the new form elements
        initFormElements();
        setupItemListeners(formCount);
    });
    
    // Set up remove buttons
    setupRemoveButtons();
    
    // Set up existing item listeners
    for (let i = 0; i < parseInt(totalForms.value); i++) {
        setupItemListeners(i);
    }
}

/**
 * Set up remove button handlers
 */
function setupRemoveButtons() {
    const removeButtons = document.querySelectorAll('.remove-form');
    
    removeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const row = this.closest('.sale-item-row');
            
            // If there's a DELETE checkbox, check it instead of removing the row
            const deleteCheckbox = row.querySelector('input[id$="-DELETE"]');
            
            if (deleteCheckbox) {
                deleteCheckbox.checked = true;
                row.style.display = 'none';
            } else {
                // Just remove the row if it's a new form
                row.remove();
            }
            
            // Update the total calculation
            updateTotalCalculation();
        });
    });
}

/**
 * Set up event listeners for each sales item row
 */
function setupItemListeners(index) {
    const drugSelect = document.getElementById(`id_saleitems-${index}-drug`);
    const quantityInput = document.getElementById(`id_saleitems-${index}-quantity`);
    
    if (!drugSelect || !quantityInput) return;
    
    // Drug selection change event
    drugSelect.addEventListener('change', function() {
        if (this.value) {
            fetchDrugInfo(this.value, index);
        } else {
            // Clear the item info if no drug is selected
            const itemInfo = document.querySelector(`#id_saleitems-${index}-drug`).closest('.sale-item-row').querySelector('.item-info');
            if (itemInfo) {
                itemInfo.style.display = 'none';
            }
            updateTotalCalculation();
        }
    });
    
    // Quantity change event
    quantityInput.addEventListener('input', function() {
        updateItemSubtotal(index);
        updateTotalCalculation();
        
        // Validate quantity against available stock
        if (drugSelect.value) {
            validateQuantityAgainstStock(index);
        }
    });
}

/**
 * Fetch drug information from the API
 */
function fetchDrugInfo(drugId, index) {
    fetch(`/api/drugs/${drugId}/info/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateDrugInfo(data, index);
        })
        .catch(error => {
            console.error('Error fetching drug info:', error);
            M.toast({html: 'Error fetching drug information', classes: 'red'});
        });
}

/**
 * Update the drug information display
 */
function updateDrugInfo(data, index) {
    const row = document.querySelector(`#id_saleitems-${index}-drug`).closest('.sale-item-row');
    const itemInfo = row.querySelector('.item-info');
    const quantityInput = document.getElementById(`id_saleitems-${index}-quantity`);
    
    if (!itemInfo) return;
    
    // Update the info card
    itemInfo.querySelector('.stock-qty').textContent = data.available_stock;
    itemInfo.querySelector('.unit-price').textContent = data.price.toFixed(2);
    
    // Calculate subtotal based on quantity
    const quantity = parseInt(quantityInput.value) || 0;
    const subtotal = quantity * data.price;
    itemInfo.querySelector('.subtotal').textContent = subtotal.toFixed(2);
    
    // Show the info card
    itemInfo.style.display = 'block';
    
    // Store price data for calculations
    row.dataset.price = data.price;
    row.dataset.stock = data.available_stock;
    
    // Validate quantity against available stock
    validateQuantityAgainstStock(index);
    
    // Update the total calculation
    updateTotalCalculation();
}

/**
 * Update an item's subtotal when quantity changes
 */
function updateItemSubtotal(index) {
    const row = document.querySelector(`#id_saleitems-${index}-drug`).closest('.sale-item-row');
    const itemInfo = row.querySelector('.item-info');
    const quantityInput = document.getElementById(`id_saleitems-${index}-quantity`);
    
    if (!itemInfo || !row.dataset.price) return;
    
    const quantity = parseInt(quantityInput.value) || 0;
    const price = parseFloat(row.dataset.price);
    const subtotal = quantity * price;
    
    itemInfo.querySelector('.subtotal').textContent = subtotal.toFixed(2);
}

/**
 * Validate quantity against available stock
 */
function validateQuantityAgainstStock(index) {
    const row = document.querySelector(`#id_saleitems-${index}-drug`).closest('.sale-item-row');
    const quantityInput = document.getElementById(`id_saleitems-${index}-quantity`);
    
    if (!row.dataset.stock || !quantityInput) return;
    
    const availableStock = parseInt(row.dataset.stock);
    const requestedQuantity = parseInt(quantityInput.value) || 0;
    
    if (requestedQuantity > availableStock) {
        quantityInput.classList.add('invalid');
        M.toast({html: `Not enough stock. Available: ${availableStock}`, classes: 'red'});
    } else {
        quantityInput.classList.remove('invalid');
    }
}

/**
 * Set up price calculation for each item
 */
function setupItemPriceCalculation() {
    // This is handled by the updateDrugInfo and updateItemSubtotal functions
}

/**
 * Update the total calculation for the entire sale
 */
function updateTotalCalculation() {
    let subtotal = 0;
    
    // Calculate subtotal from all visible items
    document.querySelectorAll('.sale-item-row').forEach(row => {
        // Skip rows marked for deletion
        const deleteCheckbox = row.querySelector('input[id$="-DELETE"]');
        if (deleteCheckbox && deleteCheckbox.checked) return;
        
        // Skip rows with no price data
        if (!row.dataset.price) return;
        
        const quantityInput = row.querySelector('input[type="number"]');
        const quantity = parseInt(quantityInput.value) || 0;
        const price = parseFloat(row.dataset.price);
        
        subtotal += quantity * price;
    });
    
    // Calculate tax (10%)
    const tax = subtotal * 0.1;
    
    // Get discount
    const discountInput = document.getElementById('id_discount');
    const discount = discountInput ? parseFloat(discountInput.value) || 0 : 0;
    
    // Calculate total
    const total = subtotal + tax - discount;
    
    // Update summary display
    document.getElementById('summary-subtotal').textContent = subtotal.toFixed(2);
    document.getElementById('summary-tax').textContent = tax.toFixed(2);
    document.getElementById('summary-discount').textContent = discount.toFixed(2);
    document.getElementById('summary-total').textContent = total.toFixed(2);
}

/**
 * Initialize select fields for drug and patient
 */
function initializeSelectFields() {
    // Auto-initialize any selected patient from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const patientId = urlParams.get('patient');
    
    if (patientId) {
        const patientSelect = document.getElementById('id_patient');
        if (patientSelect) {
            patientSelect.value = patientId;
            // Reinitialize the Materialize select
            M.FormSelect.init(patientSelect);
        }
    }
}

/**
 * Set up form validation before submission
 */
function setupFormValidation() {
    const saleForm = document.getElementById('sale-form');
    
    if (!saleForm) return;
    
    saleForm.addEventListener('submit', function(event) {
        let isValid = true;
        let hasItems = false;
        
        // Check if there are any items
        document.querySelectorAll('.sale-item-row').forEach(row => {
            // Skip rows marked for deletion
            const deleteCheckbox = row.querySelector('input[id$="-DELETE"]');
            if (deleteCheckbox && deleteCheckbox.checked) return;
            
            const drugSelect = row.querySelector('select');
            const quantityInput = row.querySelector('input[type="number"]');
            
            if (drugSelect && drugSelect.value && quantityInput && parseInt(quantityInput.value) > 0) {
                hasItems = true;
                
                // Check stock availability
                if (row.dataset.stock && parseInt(quantityInput.value) > parseInt(row.dataset.stock)) {
                    isValid = false;
                    quantityInput.classList.add('invalid');
                }
            }
        });
        
        if (!hasItems) {
            M.toast({html: 'Please add at least one item to the sale', classes: 'red'});
            isValid = false;
        }
        
        if (!isValid) {
            event.preventDefault();
            M.toast({html: 'Please correct the errors before submitting', classes: 'red'});
        }
    });
}
