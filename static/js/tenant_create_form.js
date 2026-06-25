// Auto-génération du slug et du custom domain depuis le nom
    (function() {
      const nameInput = document.getElementById('id_name');
      const slugInput = document.getElementById('id_slug');
      const servicePreview = document.getElementById('service-preview');
      const dbNameInput = document.getElementById('id_db_name');
      const customDomainInput = document.getElementById('id_custom_domain');

      let slugManuallyEdited = false;
      let domainManuallyEdited = false;

      function slugify(text) {
        return text
          .toLowerCase()
          .normalize('NFD').replace(/[\u0300-\u036f]/g, '') // supprimer accents
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/^-|-$/g, '')
          .substring(0, 30);
      }

      if (customDomainInput) {
        customDomainInput.addEventListener('input', function() {
          domainManuallyEdited = true;
        });
      }

      if (nameInput && slugInput) {
        nameInput.addEventListener('input', function() {
          if (!slugManuallyEdited) {
            const slug = slugify(this.value);
            slugInput.value = slug;
            updatePreview(slug);
          }
        });

        slugInput.addEventListener('input', function() {
          slugManuallyEdited = true;
          updatePreview(this.value);
        });
      }

      function updatePreview(slug) {
        if (servicePreview) {
          servicePreview.textContent = slug ? `paramynd-${slug}` : 'paramynd-...';
        }
        if (dbNameInput && !dbNameInput.value) {
          dbNameInput.placeholder = slug ? `paramynd_${slug.replace(/-/g,'_')}` : 'paramynd_acme';
        }
        if (customDomainInput && !domainManuallyEdited) {
          customDomainInput.value = slug ? `${slug}.paramynd.com` : '';
        }
      }
    })();

