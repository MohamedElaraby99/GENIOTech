// Function to handle session cancellation
function cancelSession(sessionId) {
    if (confirm('Are you sure you want to cancel this session?')) {
        fetch(`/sessions/${sessionId}/status`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                status: 'cancelled'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert(data.message || 'Error cancelling session');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error cancelling session');
        });
    }
}

// Function to validate session form
function validateSessionForm(form) {
    const startTime = form.querySelector('#start_time').value;
    const endTime = form.querySelector('#end_time').value;
    
    if (startTime >= endTime) {
        alert('End time must be after start time');
        return false;
    }
    
    return true;
}

// Add form validation to all session forms
document.addEventListener('DOMContentLoaded', function() {
    const addSessionForm = document.querySelector('#addSessionModal form');
    if (addSessionForm) {
        addSessionForm.addEventListener('submit', function(e) {
            if (!validateSessionForm(this)) {
                e.preventDefault();
            }
        });
    }
    
    // Add validation to edit forms
    document.querySelectorAll('[id^="editSessionModal"] form').forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateSessionForm(this)) {
                e.preventDefault();
            }
        });
    });
    
    // Set minimum date for session date inputs
    const today = new Date().toISOString().split('T')[0];
    document.querySelectorAll('input[type="date"]').forEach(input => {
        input.min = today;
    });
}); 