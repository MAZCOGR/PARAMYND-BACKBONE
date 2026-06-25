(function() {
                const minSlider = document.getElementById('min_instances');
                const maxSlider = document.getElementById('max_instances');
                const fill = document.getElementById('slider_fill');
                
                function updateFill() {
                  const min = parseInt(minSlider.value);
                  const max = parseInt(maxSlider.value);
                  const percentMin = (min / 100) * 100;
                  const percentMax = (max / 100) * 100;
                  
                  fill.style.left = percentMin + '%';
                  fill.style.width = (percentMax - percentMin) + '%';
                  
                  const minValLabel = document.getElementById('min_instances_val');
                  const maxValLabel = document.getElementById('max_instances_val');
                  if (minValLabel) minValLabel.innerText = min;
                  if (maxValLabel) maxValLabel.innerText = max;
                }

                minSlider.addEventListener('input', function() {
                  if (parseInt(minSlider.value) > parseInt(maxSlider.value)) {
                    minSlider.value = maxSlider.value;
                  }
                  updateFill();
                });

                maxSlider.addEventListener('input', function() {
                  if (parseInt(maxSlider.value) < parseInt(minSlider.value)) {
                    maxSlider.value = minSlider.value;
                  }
                  updateFill();
                });

                // Init on load
                document.addEventListener('DOMContentLoaded', updateFill);
                updateFill();
              })();



  const select = document.getElementById('deploy-tag-select');
  const preview = document.getElementById('image-uri-preview');



  // Custom select dropdown trigger & options
  const customSelectTrigger = document.getElementById('custom-select-trigger');
  const customSelectDropdown = document.getElementById('custom-select-dropdown');
  const customSelectChevron = document.getElementById('custom-select-chevron');
  const customSelectWrapper = document.getElementById('custom-select-wrapper');
  const customSelectTriggerValue = document.getElementById('custom-select-trigger-value');

  if (customSelectTrigger && customSelectDropdown) {
    customSelectTrigger.addEventListener('click', function(e) {
      e.stopPropagation();
      const isVisible = customSelectDropdown.style.display === 'block';
      customSelectDropdown.style.display = isVisible ? 'none' : 'block';
      customSelectChevron.style.transform = isVisible ? 'rotate(0deg)' : 'rotate(180deg)';
    });

    document.addEventListener('click', function(e) {
      if (customSelectWrapper && !customSelectWrapper.contains(e.target)) {
        customSelectDropdown.style.display = 'none';
        customSelectChevron.style.transform = 'rotate(0deg)';
      }
    });

    const options = customSelectDropdown.querySelectorAll('.custom-select-option');
    options.forEach(opt => {
      opt.addEventListener('click', function(e) {
        e.stopPropagation();
        const value = this.getAttribute('data-value');
        const isReady = this.getAttribute('data-ready') === 'true';
        
        select.value = value;
        const uri = this.getAttribute('data-uri');
        if (preview) preview.textContent = uri ? `URI: ${uri}` : '';
        
        let badgeHtml = isReady 
          ? `<span style="font-size:10px; padding:2px 8px; border-radius:12px; background:rgba(34,197,94,0.15); color:#22c55e; font-weight:600; text-transform:uppercase; letter-spacing:0.02em;">ready</span>`
          : `<span style="font-size:10px; padding:2px 8px; border-radius:12px; background:rgba(239,71,111,0.15); color:#ef476f; font-weight:600; text-transform:uppercase; letter-spacing:0.02em;">unavailable</span>`;
        
        customSelectTriggerValue.innerHTML = `
          <span class="td-mono" style="font-weight:600; color:#fff;">${value}</span>
          ${badgeHtml}
        `;
        
        customSelectDropdown.style.display = 'none';
        customSelectChevron.style.transform = 'rotate(0deg)';
        
        select.dispatchEvent(new Event('change'));
      });
    });
  }

  window.openDeployModal = function() {
    const modal = document.getElementById('deploy-modal');
    const box = modal.querySelector('.modal-box');
    modal.style.display = 'flex';
    void modal.offsetWidth; // force reflow
    modal.style.opacity = '1';
    box.style.transform = 'scale(1) translateY(0)';
    document.body.style.overflow = 'hidden';
  };

  window.closeDeployModal = function() {
    const modal = document.getElementById('deploy-modal');
    const box = modal.querySelector('.modal-box');
    modal.style.opacity = '0';
    box.style.transform = 'scale(0.95) translateY(10px)';
    setTimeout(() => {
      modal.style.display = 'none';
      document.body.style.overflow = '';
    }, 200);
  };

  document.getElementById('deploy-modal').addEventListener('mousedown', function(e) {
    if (e.target === this) {
      closeDeployModal();
    }
  });

  function submitDeploy() {
    const tag = select.value;
    if (!tag) {
      alert('Veuillez sélectionner une version à déployer.');
      return;
    }

    // Close the modal immediately
    closeDeployModal();

    // Show the progress card
    const progressCard = document.getElementById('deployment-progress-card');
    const tagDisplay = document.getElementById('deployment-tag-name');
    tagDisplay.textContent = tag;
    progressCard.style.display = 'block';

    // Submit the form asynchronously
    const form = document.getElementById('deploy-form');
    const formData = new FormData(form);

    fetch(form.action, {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Erreur réseau ou serveur : ' + response.status);
      }
      // Reload the page to show new state (success message from Django)
      window.location.reload();
    })
    .catch(err => {
      console.error(err);
      alert("Une erreur s'est produite pendant le déploiement. Vérifiez les logs côté serveur.");
      // On cache la barre de progression en cas d'erreur
      document.getElementById('deployment-progress-card').style.display = 'none';
    });
  }

window.openParamsModal = function() {
    const modal = document.getElementById('params-modal');
    const box = modal.querySelector('.modal-box');
    modal.style.display = 'flex';
    void modal.offsetWidth; // force reflow
    modal.style.opacity = '1';
    box.style.transform = 'scale(1) translateY(0)';
    document.body.style.overflow = 'hidden';
  };

  window.closeParamsModal = function() {
    const modal = document.getElementById('params-modal');
    const box = modal.querySelector('.modal-box');
    modal.style.opacity = '0';
    box.style.transform = 'scale(0.95) translateY(10px)';
    setTimeout(() => {
      modal.style.display = 'none';
      document.body.style.overflow = '';
    }, 200);
  };

  document.getElementById('params-modal').addEventListener('mousedown', function(e) {
    if (e.target === this) {
      closeParamsModal();
    }
  });

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      closeParamsModal();
    }
  });

