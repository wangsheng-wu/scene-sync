/**
 * Custom Select Dropdown Functionality
 * Replaces system default select elements with custom styled dropdowns
 */

// Helper function to update custom dropdown after select options change
function updateCustomDropdown(selectElement) {
    const wrapper = selectElement.parentElement;
    if (!wrapper.classList.contains('custom-dropdown')) return;
    
    const selectedText = wrapper.querySelector('.selected-text');
    const menu = wrapper.querySelector('.dropdown-menu');
    
    // Clear existing items
    menu.innerHTML = '';
    
    // Create new items
    Array.from(selectElement.options).forEach((option, index) => {
        const item = document.createElement('div');
        item.className = 'dropdown-item';
        if (option.disabled) {
            item.classList.add('disabled');
        }
        if (option.selected) {
            item.classList.add('selected');
        }
        item.textContent = option.textContent;
        item.dataset.value = option.value;
        
        item.addEventListener('click', (e) => {
            if (option.disabled) return;
            
            e.stopPropagation();
            
            // Update select value
            selectElement.value = option.value;
            selectElement.dispatchEvent(new Event('change', { bubbles: true }));
            
            // Update selected text
            selectedText.textContent = option.textContent;
            
            // Update selected state
            menu.querySelectorAll('.dropdown-item').forEach(item => item.classList.remove('selected'));
            item.classList.add('selected');
            
            // Close dropdown
            wrapper.querySelector('.dropdown-selected').classList.remove('active');
            menu.style.display = 'none';
        });
        
        menu.appendChild(item);
    });
    
    // Update selected text
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    selectedText.textContent = selectedOption ? selectedOption.textContent : 'Select an option...';
}

// Initialize custom dropdown functionality
function initializeCustomDropdowns() {
    // Find all select elements and convert them to custom dropdowns
    const selectElements = document.querySelectorAll('select');
    
    selectElements.forEach(select => {
        // Skip if already converted
        if (select.parentElement.classList.contains('custom-dropdown')) {
            return;
        }
        
        // Create custom dropdown wrapper
        const wrapper = document.createElement('div');
        wrapper.className = 'custom-dropdown';
        
        // Create selected display
        const selected = document.createElement('div');
        selected.className = 'dropdown-selected';
        
        const selectedText = document.createElement('span');
        selectedText.className = 'selected-text';
        selectedText.textContent = select.options[0] ? select.options[0].textContent : 'Select an option...';
        
        const arrow = document.createElement('i');
        arrow.className = 'fas fa-chevron-down dropdown-arrow';
        
        selected.appendChild(selectedText);
        selected.appendChild(arrow);
        
        // Create dropdown menu
        const menu = document.createElement('div');
        menu.className = 'dropdown-menu';
        
        // Create dropdown items
        Array.from(select.options).forEach((option, index) => {
            const item = document.createElement('div');
            item.className = 'dropdown-item';
            if (option.disabled) {
                item.classList.add('disabled');
            }
            if (option.selected) {
                item.classList.add('selected');
            }
            item.textContent = option.textContent;
            item.dataset.value = option.value;
            
            item.addEventListener('click', (e) => {
                if (option.disabled) return;
                
                e.stopPropagation();
                
                // Update select value
                select.value = option.value;
                select.dispatchEvent(new Event('change', { bubbles: true }));
                
                // Update selected text
                selectedText.textContent = option.textContent;
                
                // Update selected state
                menu.querySelectorAll('.dropdown-item').forEach(item => item.classList.remove('selected'));
                item.classList.add('selected');
                
                // Close dropdown
                selected.classList.remove('active');
                menu.style.display = 'none';
            });
            
            menu.appendChild(item);
        });
        
        // Add click handler to selected element
        selected.addEventListener('click', (e) => {
            e.stopPropagation();
            const isActive = selected.classList.contains('active');
            
            // Close all other dropdowns
            document.querySelectorAll('.custom-dropdown .dropdown-selected.active').forEach(el => {
                el.classList.remove('active');
                el.nextElementSibling.style.display = 'none';
            });
            
            if (!isActive) {
                selected.classList.add('active');
                menu.style.display = 'block';
            }
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!wrapper.contains(e.target)) {
                selected.classList.remove('active');
                menu.style.display = 'none';
            }
        });
        
        // Insert wrapper before select and move select inside
        select.parentNode.insertBefore(wrapper, select);
        wrapper.appendChild(select);
        wrapper.appendChild(selected);
        wrapper.appendChild(menu);
    });
}

// Export functions for use in other modules
window.CustomSelect = {
    initialize: initializeCustomDropdowns,
    update: updateCustomDropdown
};
