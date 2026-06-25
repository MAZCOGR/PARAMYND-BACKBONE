function updatePills(radio) {
          const pills = document.querySelectorAll('#filter-pills .pill');
          pills.forEach(p => {
            p.classList.remove('active');
            p.style.background = 'transparent';
            p.style.borderColor = 'rgba(255,255,255,0.1)';
          });
          const activeLabel = radio.closest('.pill');
          activeLabel.classList.add('active');
          activeLabel.style.background = 'var(--accent)';
          activeLabel.style.borderColor = 'var(--accent)';
        }
        
        // Initialiser l'état actif au chargement de la page
        document.addEventListener('DOMContentLoaded', () => {
          const checked = document.querySelector('#filter-pills input:checked');
          if(checked) updatePills(checked);
        });

window.openModal = function() {
    const modal = document.getElementById('create-tenant-modal');
    const box = modal.querySelector('.modal-box');
    modal.style.display = 'flex';
    void modal.offsetWidth; // force reflow
    modal.style.opacity = '1';
    box.style.transform = 'scale(1) translateY(0)';
    document.body.style.overflow = 'hidden';
  };

  window.closeModal = function() {
    const modal = document.getElementById('create-tenant-modal');
    const box = modal.querySelector('.modal-box');
    modal.style.opacity = '0';
    box.style.transform = 'scale(0.95) translateY(10px)';
    setTimeout(() => {
      modal.style.display = 'none';
      document.body.style.overflow = '';
    }, 200);
  };

  document.getElementById('create-tenant-modal').addEventListener('mousedown', function(e) {
    if (e.target === this) {
      closeModal();
    }
  });
  
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      closeModal();
    }
  });

