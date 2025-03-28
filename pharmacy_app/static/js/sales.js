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
    
    // Update the initial total calculation
    updateTotalCalculation();
    
    // Initialize select fields
    initializeSelectFields();
    
    // Set up form validation
    setupFormValidation();
    
    // Set up barcode scanner
    setupBarcodeScanner();
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
    itemInfo.querySelector('.unit-price').textContent = data.price.toFixed(2) + ' IQD';
    
    // Calculate subtotal based on quantity
    const quantity = parseInt(quantityInput.value) || 0;
    const subtotal = quantity * data.price;
    itemInfo.querySelector('.subtotal').textContent = subtotal.toFixed(2) + ' IQD';
    
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
    
    itemInfo.querySelector('.subtotal').textContent = subtotal.toFixed(2) + ' IQD';
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
    
    // Get tax from user input field
    const taxInput = document.getElementById('id_tax');
    let tax = 0;
    
    if (taxInput) {
        tax = parseFloat(taxInput.value) || 0;
    } else {
        // Fall back to 10% if tax field not found
        tax = subtotal * 0.1;
    }
    
    // Get discount
    const discountInput = document.getElementById('id_discount');
    const discount = discountInput ? parseFloat(discountInput.value) || 0 : 0;
    
    // Add event listeners for tax and discount inputs if they haven't been added yet
    if (taxInput && !taxInput.hasAttribute('data-has-listener')) {
        taxInput.addEventListener('input', function() {
            updateTotalCalculation();
        });
        taxInput.setAttribute('data-has-listener', 'true');
    }
    
    if (discountInput && !discountInput.hasAttribute('data-has-listener')) {
        discountInput.addEventListener('input', function() {
            updateTotalCalculation();
        });
        discountInput.setAttribute('data-has-listener', 'true');
    }
    
    // Calculate total
    const total = subtotal + tax - discount;
    
    // Update summary display
    document.getElementById('summary-subtotal').textContent = subtotal.toFixed(2) + ' IQD';
    document.getElementById('summary-tax').textContent = tax.toFixed(2) + ' IQD';
    document.getElementById('summary-discount').textContent = discount.toFixed(2) + ' IQD';
    document.getElementById('summary-total').textContent = total.toFixed(2) + ' IQD';
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
        console.log('Form submission validation - checking form');
        let isValid = true;
        let hasItems = false;
        let debugInfo = '';
        
        try {
            // Check if there are any items
            document.querySelectorAll('.sale-item-row').forEach(row => {
                // Skip rows marked for deletion
                const deleteCheckbox = row.querySelector('input[id$="-DELETE"]');
                if (deleteCheckbox && deleteCheckbox.checked) {
                    debugInfo += 'Found deleted row, skipping. ';
                    return;
                }
                
                const drugSelect = row.querySelector('select');
                const quantityInput = row.querySelector('input[type="number"]');
                
                if (drugSelect && drugSelect.value && quantityInput && parseInt(quantityInput.value) > 0) {
                    hasItems = true;
                    debugInfo += `Found valid item: drug=${drugSelect.value}, qty=${quantityInput.value}. `;
                    
                    // Check stock availability only if we have stock data
                    if (row.dataset.stock && parseInt(quantityInput.value) > parseInt(row.dataset.stock)) {
                        debugInfo += `Stock validation failed: qty=${quantityInput.value}, available=${row.dataset.stock}. `;
                        isValid = false;
                        quantityInput.classList.add('invalid');
                        M.toast({html: `Not enough stock for selected drug. Available: ${row.dataset.stock}`, classes: 'red'});
                    }
                } else if (drugSelect && drugSelect.value) {
                    debugInfo += `Found drug but invalid quantity: drug=${drugSelect.value}, qty=${quantityInput ? quantityInput.value : 'missing'}. `;
                } else if (quantityInput && parseInt(quantityInput.value) > 0) {
                    debugInfo += `Found quantity but no drug selected: qty=${quantityInput.value}. `;
                }
            });
            
            if (!hasItems) {
                debugInfo += 'No valid items found. ';
                M.toast({html: 'Please add at least one item to the sale', classes: 'red'});
                isValid = false;
            }
            
            // Check if patient is selected (unless walk-in is checked)
            const patientSelect = document.getElementById('id_patient');
            const walkInCheckbox = document.getElementById('id_use_walk_in');
            
            if (patientSelect && !patientSelect.value && !(walkInCheckbox && walkInCheckbox.checked)) {
                debugInfo += 'No patient selected. ';
                M.toast({html: 'Please select a patient or check Walk-In Customer', classes: 'red'});
                isValid = false;
            } else {
                if (walkInCheckbox && walkInCheckbox.checked) {
                    debugInfo += 'Walk-in customer selected. ';
                } else {
                    debugInfo += `Patient selected: ${patientSelect ? patientSelect.value : 'missing field'}. `;
                }
            }
            
            if (!isValid) {
                console.log('Form validation failed: ' + debugInfo);
                event.preventDefault();
                M.toast({html: 'Please correct the errors before submitting', classes: 'red'});
            } else {
                console.log('Form validation successful: ' + debugInfo);
                // Make sure form actually submits - allow normal browser submission
            }
        } catch(error) {
            // If any error occurs in validation, log it but allow form to submit normally
            console.error('Error during form validation:', error);
            console.log('Allowing form submission despite validation error');
            // Don't prevent default - let the server validate
        }
    });
}

/**
 * Set up barcode scanner functionality
 */
function setupBarcodeScanner() {
    const barcodeInput = document.getElementById('barcode_scanner');
    if (!barcodeInput) return;
    
    // Add helper text to indicate barcode is optional
    const helperText = document.createElement('span');
    helperText.className = 'helper-text';
    helperText.textContent = '(Optional) You can also add items manually using the dropdown below';
    barcodeInput.parentNode.appendChild(helperText);
    
    // Handle barcode input
    barcodeInput.addEventListener('keydown', function(e) {
        // Enter key
        if (e.key === 'Enter') {
            e.preventDefault();
            const barcode = this.value.trim();
            
            if (barcode) {
                fetchDrugByBarcode(barcode);
                this.value = ''; // Clear the input
            }
        }
    });
    
    // Add a dedicated scanner button
    const scannerIcon = barcodeInput.previousElementSibling;
    if (scannerIcon) {
        scannerIcon.style.cursor = 'pointer';
        scannerIcon.addEventListener('click', function() {
            barcodeInput.focus();
        });
    }
    
    // Remove auto-focus behavior to make it clear barcode is optional
    // The user can click on the scanner icon or field when they want to use it
}

/**
 * Fetch drug information by barcode
 */
function fetchDrugByBarcode(barcode) {
    console.log('Fetching drug by barcode:', barcode);
    
    // Show a toast to indicate the scanning is in progress
    M.toast({html: `Scanning barcode: ${barcode}...`, classes: 'blue'});
    
    fetch(`/api/drugs/barcode/?barcode=${encodeURIComponent(barcode)}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json',
        },
        credentials: 'same-origin'
    })
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('No drug found with this barcode');
                } else if (response.status === 302) {
                    throw new Error('Redirected. You may need to log in again.');
                }
                throw new Error(`Network response was not ok: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Barcode API response:', data);
            if (data.success) {
                addDrugToForm(data);
                M.toast({html: `Found drug: ${data.name}`, classes: 'green'});
            } else {
                M.toast({html: data.error || 'Error processing barcode', classes: 'red'});
            }
        })
        .catch(error => {
            console.error('Error fetching drug by barcode:', error);
            M.toast({html: error.message || 'Error fetching drug by barcode', classes: 'red'});
        });
}

/**
 * Add a drug to the form using data from the barcode scan
 */
function addDrugToForm(drugData) {
    console.log('Adding drug to form:', drugData);
    
    if (!drugData || !drugData.id) {
        console.error('Invalid drug data:', drugData);
        M.toast({html: 'Error: Invalid drug data', classes: 'red'});
        return;
    }
    
    // Check if drug is already in the form
    let existingRow = null;
    let existingIndex = -1;
    
    document.querySelectorAll('.sale-item-row').forEach((row, index) => {
        // Skip rows marked for deletion
        const deleteCheckbox = row.querySelector('input[id$="-DELETE"]');
        if (deleteCheckbox && deleteCheckbox.checked) return;
        
        const drugSelect = row.querySelector('select');
        if (drugSelect && drugSelect.value === drugData.id.toString()) {
            existingRow = row;
            existingIndex = index;
        }
    });
    
    if (existingRow) {
        console.log('Updating existing item at index:', existingIndex);
        // Update quantity of existing item
        const quantityInput = document.getElementById(`id_saleitems-${existingIndex}-quantity`);
        if (quantityInput) {
            const currentQty = parseInt(quantityInput.value) || 0;
            const newQty = currentQty + 1;
            quantityInput.value = newQty;
            
            // Trigger the input event to update calculations
            const event = new Event('input', { bubbles: true });
            quantityInput.dispatchEvent(event);
            
            // Update the item's data attributes
            const row = quantityInput.closest('.sale-item-row');
            if (row) {
                row.dataset.price = drugData.price;
                row.dataset.stock = drugData.available_stock;
            }
            
            M.toast({html: `Added ${drugData.name} (now ${newQty})`, classes: 'green'});
        }
    } else {
        console.log('Adding new item');
        // Add new item
        const addButton = document.getElementById('add-more');
        if (addButton) {
            try {
                // First click the add button to create a new row
                addButton.click();
                
                // Get the index of the new row
                const totalForms = document.getElementById('id_saleitems-TOTAL_FORMS');
                if (!totalForms) {
                    throw new Error('Could not find TOTAL_FORMS element');
                }
                
                const newIndex = parseInt(totalForms.value) - 1;
                console.log('New item index:', newIndex);
                
                // Set the drug and quantity
                const drugSelect = document.getElementById(`id_saleitems-${newIndex}-drug`);
                const quantityInput = document.getElementById(`id_saleitems-${newIndex}-quantity`);
                
                if (!drugSelect) {
                    throw new Error(`Could not find drug select field for index ${newIndex}`);
                }
                
                if (!quantityInput) {
                    throw new Error(`Could not find quantity input field for index ${newIndex}`);
                }
                
                // Set values
                drugSelect.value = drugData.id;
                quantityInput.value = 1;
                
                // Update the select with Materialize
                M.FormSelect.init(drugSelect);
                
                // Store data in the row for calculations
                const row = drugSelect.closest('.sale-item-row');
                if (row) {
                    row.dataset.price = drugData.price;
                    row.dataset.stock = drugData.available_stock;
                }
                
                // Update the item info display
                const itemInfo = row.querySelector('.item-info');
                if (itemInfo) {
                    itemInfo.querySelector('.stock-qty').textContent = drugData.available_stock;
                    itemInfo.querySelector('.unit-price').textContent = drugData.price.toFixed(2) + ' IQD';
                    itemInfo.querySelector('.subtotal').textContent = drugData.price.toFixed(2) + ' IQD';
                    itemInfo.style.display = 'block';
                }
                
                // Trigger the change event to fetch drug info
                const changeEvent = new Event('change', { bubbles: true });
                drugSelect.dispatchEvent(changeEvent);
                
                // Update total calculation
                updateTotalCalculation();
                
                M.toast({html: `Added ${drugData.name}`, classes: 'green'});
            } catch (error) {
                console.error('Error adding drug to form:', error);
                M.toast({html: `Error adding drug: ${error.message}`, classes: 'red'});
            }
        } else {
            console.error('Could not find add button');
            M.toast({html: 'Error: Could not find add button', classes: 'red'});
        }
    }
}
