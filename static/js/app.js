// GENIOTECH JavaScript functionality

document.addEventListener("DOMContentLoaded", function () {
  initializeApp();
});

function initializeApp() {
  // Initialize tooltips
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Initialize popovers
  var popoverTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="popover"]')
  );
  var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });

  // Auto-hide alerts after 5 seconds
  setTimeout(function () {
    var alerts = document.querySelectorAll(".alert-dismissible");
    alerts.forEach(function (alert) {
      var bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    });
  }, 5000);

  // Initialize search functionality
  initializeSearch();

  // Initialize form validations
  initializeFormValidation();

  // Initialize dashboard updates
  if (document.querySelector(".dashboard")) {
    initializeDashboard();
  }
}

// Search functionality
function initializeSearch() {
  const searchInputs = document.querySelectorAll(
    'input[id*="search"], input[placeholder*="search"], input[placeholder*="Search"]'
  );

  searchInputs.forEach(function (input) {
    input.addEventListener("input", function (e) {
      debounce(performSearch, 300)(e.target.value, e.target);
    });
  });
}

// Debounce function for search
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Perform search operation
function performSearch(query, inputElement) {
  const tableId =
    inputElement.getAttribute("data-table") || findNearestTable(inputElement);
  if (tableId) {
    filterTable(tableId, query);
  }
}

// Find nearest table to search input
function findNearestTable(element) {
  const card = element.closest(".card");
  if (card) {
    const table = card.querySelector("table");
    return table ? table.id : null;
  }
  return null;
}

// Filter table rows based on search query
function filterTable(tableId, query) {
  const table = document.getElementById(tableId);
  if (!table) return;

  const rows = table.querySelectorAll("tbody tr");
  const searchTerm = query.toLowerCase();

  rows.forEach(function (row) {
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(searchTerm) ? "" : "none";
  });

  // Update row count display if exists
  updateRowCount(tableId, rows);
}

// Update row count display
function updateRowCount(tableId, rows) {
  const visibleCount = Array.from(rows).filter(
    (row) => row.style.display !== "none"
  ).length;
  const totalCount = rows.length;

  const countElement = document.querySelector(
    `[data-table-count="${tableId}"]`
  );
  if (countElement) {
    countElement.textContent = `Showing ${visibleCount} of ${totalCount}`;
  }
}

// Form validation
function initializeFormValidation() {
  const forms = document.querySelectorAll("form[novalidate]");

  forms.forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    });
  });

  // Real-time validation for inputs
  const inputs = document.querySelectorAll(
    "input[required], select[required], textarea[required]"
  );
  inputs.forEach(function (input) {
    input.addEventListener("blur", function () {
      validateField(input);
    });

    input.addEventListener("input", function () {
      if (input.classList.contains("is-invalid")) {
        validateField(input);
      }
    });
  });
}

// Validate individual field
function validateField(field) {
  const isValid = field.checkValidity();
  field.classList.toggle("is-valid", isValid);
  field.classList.toggle("is-invalid", !isValid);

  // Show/hide custom error message
  const errorElement = field.parentNode.querySelector(".invalid-feedback");
  if (errorElement) {
    errorElement.style.display = isValid ? "none" : "block";
  }
}

// Dashboard functionality
function initializeDashboard() {
  // Refresh dashboard data every 5 minutes
  setInterval(refreshDashboardStats, 300000);

  // Initialize any charts or graphs
  initializeCharts();
}

// Refresh dashboard statistics
function refreshDashboardStats() {
  fetch("/api/dashboard_stats")
    .then((response) => response.json())
    .then((data) => {
      updateDashboardElements(data);
    })
    .catch((error) => {
      console.error("Error refreshing dashboard stats:", error);
    });
}

// Update dashboard elements with new data
function updateDashboardElements(data) {
  Object.keys(data).forEach(function (key) {
    const element = document.getElementById(key.replace("_", "-"));
    if (element) {
      animateNumber(element, parseInt(element.textContent) || 0, data[key]);
    }
  });
}

// Animate number changes
function animateNumber(element, start, end) {
  const duration = 1000;
  const range = end - start;
  const increment = range / (duration / 16);
  let current = start;

  const timer = setInterval(function () {
    current += increment;
    if (
      (increment > 0 && current >= end) ||
      (increment < 0 && current <= end)
    ) {
      current = end;
      clearInterval(timer);
    }
    element.textContent = Math.floor(current);
  }, 16);
}

// Initialize charts (placeholder for future chart implementation)
function initializeCharts() {
  // This would be where we initialize Chart.js or other charting libraries
  console.log("Charts initialized");
}

// Utility functions
function showNotification(message, type = "info") {
  // Create and show bootstrap toast notification
  const toastContainer =
    document.getElementById("toast-container") || createToastContainer();
  const toast = createToast(message, type);
  toastContainer.appendChild(toast);

  const bsToast = new bootstrap.Toast(toast);
  bsToast.show();

  // Remove toast after it hides
  toast.addEventListener("hidden.bs.toast", function () {
    toast.remove();
  });
}

function createToastContainer() {
  const container = document.createElement("div");
  container.id = "toast-container";
  container.className = "toast-container position-fixed top-0 end-0 p-3";
  container.style.zIndex = "1055";
  document.body.appendChild(container);
  return container;
}

function createToast(message, type) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.setAttribute("role", "alert");
  toast.innerHTML = `
        <div class="toast-header">
            <i class="fas fa-${getIconForType(type)} me-2"></i>
            <strong class="me-auto">${getHeaderForType(type)}</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
  return toast;
}

function getIconForType(type) {
  const icons = {
    success: "check-circle",
    error: "exclamation-triangle",
    warning: "exclamation-triangle",
    info: "info-circle",
  };
  return icons[type] || icons["info"];
}

function getHeaderForType(type) {
  const headers = {
    success: "Success",
    error: "Error",
    warning: "Warning",
    info: "Information",
  };
  return headers[type] || headers["info"];
}

// AJAX form submission helper
function submitFormAjax(form, successCallback, errorCallback) {
  const formData = new FormData(form);

  fetch(form.action, {
    method: form.method,
    body: formData,
    headers: {
      "X-Requested-With": "XMLHttpRequest",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        if (successCallback) successCallback(data);
        showNotification(
          data.message || "Operation completed successfully",
          "success"
        );
      } else {
        if (errorCallback) errorCallback(data);
        showNotification(data.message || "An error occurred", "error");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      if (errorCallback) errorCallback(error);
      showNotification("Network error occurred", "error");
    });
}

// Format date helper
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString() + " " + date.toLocaleTimeString();
}

// Confirm action helper
function confirmAction(message, callback) {
  if (confirm(message)) {
    callback();
  }
}

// Export functions for global use
window.CRM = {
  showNotification: showNotification,
  submitFormAjax: submitFormAjax,
  formatDate: formatDate,
  confirmAction: confirmAction,
  refreshDashboardStats: refreshDashboardStats,
};
