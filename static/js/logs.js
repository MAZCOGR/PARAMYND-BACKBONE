document.addEventListener('DOMContentLoaded', () => {
  const triggers = document.querySelectorAll('.custom-select-trigger');
  
  triggers.forEach(trigger => {
    trigger.addEventListener('click', function(e) {
      e.stopPropagation();
      const targetId = this.getAttribute('data-target');
      const dropdown = document.getElementById(targetId);
      const chevron = this.querySelector('.custom-select-chevron');
      
      const isVisible = dropdown.style.display === 'block';
      
      // Hide all other dropdowns
      document.querySelectorAll('.custom-select-dropdown').forEach(d => {
        d.style.display = 'none';
      });
      document.querySelectorAll('.custom-select-chevron').forEach(c => {
        c.style.transform = 'rotate(0deg)';
      });

      // Toggle current
      if (!isVisible) {
        dropdown.style.display = 'block';
        chevron.style.transform = 'rotate(180deg)';
      }
    });
  });

  // Close dropdowns when clicking outside
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.custom-select-wrapper')) {
      document.querySelectorAll('.custom-select-dropdown').forEach(d => {
        d.style.display = 'none';
      });
      document.querySelectorAll('.custom-select-chevron').forEach(c => {
        c.style.transform = 'rotate(0deg)';
      });
    }
  });

  // Handle option selection
  const options = document.querySelectorAll('.custom-select-option');
  options.forEach(opt => {
    opt.addEventListener('click', function(e) {
      e.stopPropagation();
      const value = this.getAttribute('data-value');
      const inputId = this.getAttribute('data-input');
      const inputEl = document.getElementById(inputId);
      
      if (inputEl) {
        // Set the hidden input value
        inputEl.value = value;
        // Submit the form
        const form = document.getElementById('logs-filter-form');
        if (form) {
          form.submit();
        }
      }
    });
  });
});

function refreshLogs() {
  window.location.reload();
}
