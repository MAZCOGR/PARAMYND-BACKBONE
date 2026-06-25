// Use event delegation to handle clicks, so it works perfectly with HTMX
document.addEventListener('click', function(e) {
  // 1. Handle Trigger Clicks
  const trigger = e.target.closest('.custom-select-trigger');
  if (trigger) {
    e.stopPropagation();
    const targetId = trigger.getAttribute('data-target');
    const dropdown = document.getElementById(targetId);
    if (!dropdown) return;

    const chevron = trigger.querySelector('.custom-select-chevron');
    const isVisible = dropdown.style.display === 'block';
    
    // Hide all other dropdowns
    document.querySelectorAll('.custom-select-dropdown').forEach(d => {
      d.style.display = 'none';
    });
    document.querySelectorAll('.custom-select-chevron').forEach(c => {
      if (c) c.style.transform = 'rotate(0deg)';
    });

    // Toggle current
    if (!isVisible) {
      dropdown.style.display = 'block';
      if (chevron) chevron.style.transform = 'rotate(180deg)';
    }
    return;
  }

  // 2. Handle Option Selection
  const option = e.target.closest('.custom-select-option');
  if (option) {
    e.stopPropagation();
    const value = option.getAttribute('data-value');
    const inputId = option.getAttribute('data-input');
    const inputEl = document.getElementById(inputId);
    
    if (inputEl) {
      inputEl.value = value;
      const form = document.getElementById('logs-filter-form');
      if (form) {
        form.submit();
      }
    }
    return;
  }

  // 3. Close dropdowns when clicking outside
  if (!e.target.closest('.custom-select-wrapper')) {
    document.querySelectorAll('.custom-select-dropdown').forEach(d => {
      d.style.display = 'none';
    });
    document.querySelectorAll('.custom-select-chevron').forEach(c => {
      if (c) c.style.transform = 'rotate(0deg)';
    });
  }
});

function refreshLogs() {
  window.location.reload();
}
