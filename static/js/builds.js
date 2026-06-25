function getCsrfToken() {
    const el = document.querySelector('[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
}
function toggleActionMenu(btn, buildId) {
    document.querySelectorAll('.action-dropdown').forEach(el => {
        if(el.id !== 'action-menu-' + buildId) el.style.display = 'none';
    });
    const menu = document.getElementById('action-menu-' + buildId);
    menu.style.display = menu.style.display === 'none' ? 'flex' : 'none';
}

document.addEventListener('click', function(e) {
    if (!e.target.closest('.action-menu-wrapper')) {
        document.querySelectorAll('.action-dropdown').forEach(el => el.style.display = 'none');
    }
});

function confirmDelete(buildId) {
    showCustomConfirm(
        "Voulez-vous vraiment supprimer ce build pour libérer de l'espace ?",
        "Supprimer",
        () => {
            fetch(`/tenants/builds/${buildId}/delete/`, {
                method: 'POST',
                headers: {'X-CSRFToken': getCsrfToken()}
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    location.reload();
                } else {
                    alert("Erreur: " + data.error);
                }
            });
        }
    );
}

function confirmRollback(buildId, commitSha) {
    showCustomConfirm(
        `Voulez-vous restaurer la version du commit ${commitSha} sur le backbone ?`,
        "Restaurer",
        () => {
            fetch(`/tenants/builds/${buildId}/rollback/`, {
                method: 'POST',
                headers: {'X-CSRFToken': getCsrfToken()}
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    location.reload();
                } else {
                    alert("Erreur: " + data.error);
                }
            });
        }
    );
}
