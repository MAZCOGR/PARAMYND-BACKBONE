document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    const toasts = document.querySelectorAll('.toast-message');
    toasts.forEach(toast => {
      toast.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px) scale(0.95)';
      setTimeout(() => {
        const parent = toast.parentElement;
        toast.remove();
        if (parent && parent.children.length === 0) parent.remove();
      }, 400);
    });
  }, 4500);
});

function showCustomConfirm(message, actionLabel, actionCallback) {
    const modal = document.getElementById('custom-confirm-modal');
    if (!modal) return;
    const box = modal.querySelector('.confirm-box');
    document.getElementById('confirm-message').textContent = message;
    
    const okBtn = document.getElementById('confirm-ok-btn');
    okBtn.textContent = actionLabel;
    
    if (actionLabel === 'Supprimer') {
        okBtn.style.background = 'var(--danger)';
    } else {
        okBtn.style.background = 'var(--accent)';
    }

    modal.style.display = 'flex';
    void modal.offsetWidth; // Trigger reflow
    modal.style.opacity = '1';
    box.style.transform = 'scale(1)';

    const cleanup = () => {
        modal.style.opacity = '0';
        box.style.transform = 'scale(0.95)';
        setTimeout(() => modal.style.display = 'none', 200);
        document.getElementById('confirm-cancel-btn').removeEventListener('click', handleCancel);
        okBtn.removeEventListener('click', handleOk);
    };

    const handleCancel = () => cleanup();
    const handleOk = () => {
        cleanup();
        actionCallback();
    };

    document.getElementById('confirm-cancel-btn').addEventListener('click', handleCancel);
    okBtn.addEventListener('click', handleOk);
}
