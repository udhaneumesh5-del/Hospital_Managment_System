// Global Functions for Hospital Management System

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2
    }).format(amount);
}

// Format date
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-IN', options);
}

// Validate email
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Validate phone number (Indian format)
function validatePhone(phone) {
    const re = /^[6-9]\d{9}$/;
    return re.test(phone);
}

// Show confirmation dialog
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Auto-hide flash messages
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
    
    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(el => {
        el.addEventListener('mouseenter', showTooltip);
        el.addEventListener('mouseleave', hideTooltip);
    });
    
    // Initialize modals
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        const closeBtn = modal.querySelector('.close-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => modal.style.display = 'none');
        }
    });
});

// Tooltip functions
function showTooltip(e) {
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = e.target.getAttribute('data-tooltip');
    document.body.appendChild(tooltip);
    
    const rect = e.target.getBoundingClientRect();
    tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    
    e.target._tooltip = tooltip;
}

function hideTooltip(e) {
    if (e.target._tooltip) {
        e.target._tooltip.remove();
        delete e.target._tooltip;
    }
}

// Search functionality for tables
function searchTable() {
    const input = document.getElementById('searchInput');
    const filter = input.value.toUpperCase();
    const table = document.getElementById('dataTable');
    const rows = table.getElementsByTagName('tr');
    
    for (let i = 1; i < rows.length; i++) {
        const cells = rows[i].getElementsByTagName('td');
        let found = false;
        
        for (let j = 0; j < cells.length; j++) {
            const cell = cells[j];
            if (cell) {
                const textValue = cell.textContent || cell.innerText;
                if (textValue.toUpperCase().indexOf(filter) > -1) {
                    found = true;
                    break;
                }
            }
        }
        
        rows[i].style.display = found ? '' : 'none';
    }
}

// Print functionality
function printSection(elementId) {
    const printContent = document.getElementById(elementId).innerHTML;
    const originalContent = document.body.innerHTML;
    
    document.body.innerHTML = printContent;
    window.print();
    document.body.innerHTML = originalContent;
    location.reload();
}

// Export to CSV
function exportToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll('tr');
    const csv = [];
    
    rows.forEach(row => {
        const cells = row.querySelectorAll('th, td');
        const rowData = Array.from(cells).map(cell => cell.textContent.trim());
        csv.push(rowData.join(','));
    });
    
    const blob = new Blob([csv.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}

// AJAX request helper
async function fetchAPI(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showNotification('An error occurred. Please try again.', 'error');
        return null;
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <span class="notification-icon">${type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ'}</span>
        <span class="notification-message">${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('error');
            isValid = false;
        } else {
            input.classList.remove('error');
        }
        
        // Email validation
        if (input.type === 'email' && input.value) {
            if (!validateEmail(input.value)) {
                input.classList.add('error');
                isValid = false;
            }
        }
        
        // Phone validation
        if (input.type === 'tel' && input.value) {
            if (!validatePhone(input.value)) {
                input.classList.add('error');
                isValid = false;
            }
        }
    });
    
    if (!isValid) {
        showNotification('Please fill all required fields correctly.', 'error');
    }
    
    return isValid;
}

// Dynamic doctor loading based on department
async function loadDoctorsByDepartment(departmentId, selectElementId) {
    const select = document.getElementById(selectElementId);
    if (!select) return;
    
    select.innerHTML = '<option value="">Loading...</option>';
    
    const doctors = await fetchAPI(`/api/doctors/by-department/${departmentId}`);
    
    if (doctors && doctors.length) {
        select.innerHTML = '<option value="">Select Doctor</option>';
        doctors.forEach(doctor => {
            const option = document.createElement('option');
            option.value = doctor.doctor_id;
            option.textContent = `Dr. ${doctor.first_name} ${doctor.last_name} - ${doctor.specialization}`;
            select.appendChild(option);
        });
    } else {
        select.innerHTML = '<option value="">No doctors available</option>';
    }
}

// Load available time slots
async function loadTimeSlots(doctorId, date, selectElementId) {
    const select = document.getElementById(selectElementId);
    if (!select) return;
    
    select.innerHTML = '<option value="">Loading slots...</option>';
    
    const slots = await fetchAPI(`/api/appointments/slots?doctor_id=${doctorId}&date=${date}`);
    
    if (slots && slots.length) {
        select.innerHTML = '<option value="">Select Time</option>';
        slots.forEach(slot => {
            const option = document.createElement('option');
            option.value = slot.time;
            option.textContent = slot.time;
            if (!slot.available) {
                option.disabled = true;
                option.textContent += ' (Booked)';
            }
            select.appendChild(option);
        });
    } else {
        select.innerHTML = '<option value="">No slots available</option>';
    }
}

// Calculate bill total dynamically
function calculateBillTotal() {
    const items = document.querySelectorAll('.bill-item');
    let subtotal = 0;
    
    items.forEach(item => {
        const quantity = parseFloat(item.querySelector('.quantity')?.value || 0);
        const price = parseFloat(item.querySelector('.price')?.value || 0);
        const total = quantity * price;
        subtotal += total;
        
        const totalCell = item.querySelector('.item-total');
        if (totalCell) totalCell.textContent = formatCurrency(total);
    });
    
    const tax = subtotal * 0.18;
    const total = subtotal + tax;
    
    document.getElementById('subtotal').textContent = formatCurrency(subtotal);
    document.getElementById('tax').textContent = formatCurrency(tax);
    document.getElementById('total').textContent = formatCurrency(total);
    
    return total;
}

// Add bill item row
function addBillItem() {
    const container = document.getElementById('bill-items-container');
    const template = document.getElementById('bill-item-template');
    
    if (container && template) {
        const newItem = template.content.cloneNode(true);
        container.appendChild(newItem);
    }
}

// Remove bill item
function removeBillItem(button) {
    const item = button.closest('.bill-item');
    if (item) {
        item.remove();
        calculateBillTotal();
    }
}

// Initialize date pickers with min date
document.addEventListener('DOMContentLoaded', function() {
    const datePickers = document.querySelectorAll('input[type="date"]');
    const today = new Date().toISOString().split('T')[0];
    
    datePickers.forEach(picker => {
        if (!picker.value) {
            picker.min = today;
        }
    });
});

// Toggle sidebar on mobile
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

// Progress bar animation
function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const width = bar.getAttribute('data-width');
        if (width) {
            setTimeout(() => {
                bar.style.width = width + '%';
            }, 100);
        }
    });
}

// Countdown timer for appointments
function startCountdown(elementId, targetTime) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const timer = setInterval(() => {
        const now = new Date().getTime();
        const distance = targetTime - now;
        
        if (distance < 0) {
            clearInterval(timer);
            element.innerHTML = "EXPIRED";
            return;
        }
        
        const hours = Math.floor(distance / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        element.innerHTML = `${hours}h ${minutes}m ${seconds}s`;
    }, 1000);
}

// Export all functions globally
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;
window.validateEmail = validateEmail;
window.validatePhone = validatePhone;
window.confirmAction = confirmAction;
window.searchTable = searchTable;
window.printSection = printSection;
window.exportToCSV = exportToCSV;
window.showNotification = showNotification;
window.validateForm = validateForm;
window.loadDoctorsByDepartment = loadDoctorsByDepartment;
window.loadTimeSlots = loadTimeSlots;
window.calculateBillTotal = calculateBillTotal;
window.addBillItem = addBillItem;
window.removeBillItem = removeBillItem;
window.toggleSidebar = toggleSidebar;