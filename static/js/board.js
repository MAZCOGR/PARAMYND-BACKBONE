
// ── Utilities ─────────────────────────────────────────
window._graphCSRF = () => (document.querySelector('[name=csrfmiddlewaretoken]') || {}).value || '';
window._graphPost = (url, data) => fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': window._graphCSRF() },
    body: Object.entries(data).map(([k,v]) => `${k}=${encodeURIComponent(v)}`).join('&')
});

// ── Drawing ───────────────────────────────────────────
window._graphNodeCenter = function(el) {
    const x = parseFloat(el.style.left) || 0;
    const y = parseFloat(el.style.top)  || 0;
    const sizes = { project: [240, 88], sprint: [210, 72], task: [420, 68] };
    const [w, h] = sizes[el.dataset.type] || [200, 80];
    return { x: x + w/2, y: y + h/2, w, h };
};

window._graphNodeConnectionPoint = function(el, targetCenter) {
    const { x: cx, y: cy, w, h } = window._graphNodeCenter(el);
    const pts = [
        { x: cx, y: cy - h/2, dirX: 0, dirY: -1 }, // top
        { x: cx, y: cy + h/2, dirX: 0, dirY: 1 },  // bottom
        { x: cx - w/2, y: cy, dirX: -1, dirY: 0 }, // left
        { x: cx + w/2, y: cy, dirX: 1, dirY: 0 }   // right
    ];
    let best = pts[0], minDist = Infinity;
    pts.forEach(p => {
        const d = Math.hypot(targetCenter.x - p.x, targetCenter.y - p.y);
        if (d < minDist) { minDist = d; best = p; }
    });
    return best;
};

window._graphDrawBezier = function(svg, p1, p2, opts) {
    opts = opts || {};
    const dist = Math.hypot(p2.x - p1.x, p2.y - p1.y);
    const weight = dist * 0.4;
    
    const cp1x = p1.x + p1.dirX * weight;
    const cp1y = p1.y + p1.dirY * weight;
    const cp2x = p2.x + p2.dirX * weight;
    const cp2y = p2.y + p2.dirY * weight;
    
    const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    p.setAttribute('d', `M ${p1.x} ${p1.y} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`);
    p.setAttribute('fill', 'none');
    p.setAttribute('stroke', opts.stroke || 'rgba(124,92,252,0.4)');
    p.setAttribute('stroke-width', opts.w || '2');
    if (opts.dash) p.setAttribute('stroke-dasharray', opts.dash);
    p.style.pointerEvents = opts.clickable ? 'stroke' : 'none';
    if (opts.clickable) p.style.cursor = 'pointer';
    svg.appendChild(p);
    return p;
};

window._graphDrawLines = function(previewTask, previewSprint) {
    const svg = document.getElementById('canvas-svg');
    if (!svg) return;
    svg.innerHTML = '';
    const nc = window._graphNodeCenter;
    const cp = window._graphNodeConnectionPoint;
    const db = window._graphDrawBezier;

    // 1. Sprint → Project (solid purple)
    window._graphSPLinks.forEach(({ sprintId, projectId }) => {
        const s = document.getElementById(`sprint-${sprintId}`);
        const p = document.getElementById(`proj-${projectId}`);
        if (!s || !p || s.style.display === 'none' || p.style.display === 'none') return;
        db(svg, cp(p, nc(s)), cp(s, nc(p)), { stroke: 'rgba(124,92,252,0.55)', w: '2' });
    });

    // 2. Task → Sprint (dashed teal)
    Object.entries(window._graphTSLinks).forEach(([taskId, sprintId]) => {
        if (previewTask && previewTask.dataset.id == taskId) return;
        const t = document.getElementById(`task-${taskId}`);
        const s = document.getElementById(`sprint-${sprintId}`);
        if (!t || !s || t.style.display === 'none' || s.style.display === 'none') return;
        const pathEl = db(svg, cp(s, nc(t)), cp(t, nc(s)), { stroke: 'rgba(6,214,160,0.5)', w: '1.5', dash: '6,4', clickable: true });
        pathEl.onmouseenter = () => { pathEl.setAttribute('stroke', '#ef4444'); pathEl.setAttribute('stroke-width', '4'); };
        pathEl.onmouseleave = () => { pathEl.setAttribute('stroke', 'rgba(6,214,160,0.5)'); pathEl.setAttribute('stroke-width', '1.5'); };
        pathEl.onclick = () => {
            if (confirm('Voulez-vous détacher cette tâche du sprint ?')) {
                delete window._graphTSLinks[taskId];
                
                // Update select dropdown
                const selectEl = document.getElementById(`task-sprint-select-${taskId}`);
                if (selectEl) selectEl.value = '';
                
                const lbl = document.getElementById(`task-sprint-label-${taskId}`);
                if (lbl) lbl.textContent = '—';
                
                window._graphPost('/projects/task/link-sprint/', { task_id: taskId, sprint_id: '' });
                window._graphDrawLines();
            }
        };
    });
};

// ── Init (HTMX-safe with AbortController cleanup) ─────
window._graphInit = function() {
    const wrapper = document.getElementById('canvas-wrapper');
    const inner   = document.getElementById('canvas-inner');
    if (!wrapper || !inner) return;

    // Cancel previous document-level listeners to avoid accumulation
    if (window._graphAbortCtrl) window._graphAbortCtrl.abort();
    window._graphAbortCtrl = new AbortController();
    const sig = window._graphAbortCtrl.signal;

    // ── Zoom & Pan state ────────────────────
    window._graphZoom = window._graphZoom || 1;
    window._graphTX   = window._graphTX || 0;
    window._graphTY   = window._graphTY || 0;

    const applyTransform = () => {
        inner.style.transform = `translate(${window._graphTX}px, ${window._graphTY}px) scale(${window._graphZoom})`;
    };
    applyTransform();

    const allNodes    = [...wrapper.querySelectorAll('.gnode')];
    const sprintNodes = [...wrapper.querySelectorAll('.gnode-sprint')];

    // Helpers: convert screen pos → canvas pos
    const toCanvas = (cx, cy) => {
        const r = wrapper.getBoundingClientRect();
        return {
            x: (cx - r.left - window._graphTX) / window._graphZoom,
            y: (cy - r.top  - window._graphTY) / window._graphZoom
        };
    };

    // ── Document level clicks ────────
    document.addEventListener('mousedown', e => {
        // Close expanded tasks
        if (!e.target.closest('.gnode-task') && !e.target.closest('.task-toggle-btn')) {
            let changed = false;
            document.querySelectorAll('.gnode-task.expanded').forEach(n => {
                n.classList.remove('expanded');
                changed = true;
            });
            if (changed) setTimeout(window._graphDrawLines, 300);
        }

        // Clear selection if clicking on background
        if (!e.target.closest('.gnode') && !e.target.closest('.task-toggle-btn')) {
            document.querySelectorAll('.gnode.selected').forEach(n => n.classList.remove('selected'));
        }
    }, { signal: sig });

    // ── NODE DRAG ──────────────────────────────────────────────────────
    let dragging = null;

    allNodes.forEach(node => {
        node.addEventListener('mousedown', e => {
            if (e.button !== 0 || window._graphSpaceDown) return;  // left button only, not panning
            if (['BUTTON','SELECT','OPTION','SPAN','TEXTAREA','INPUT'].includes(e.target.tagName)) return;
            window.closeAllPopups && window.closeAllPopups();
            e.preventDefault();
            
            // Multi-selection with Ctrl
            if (e.ctrlKey || e.metaKey) {
                node.classList.toggle('selected');
                return; // Do not start drag
            }
            
            // If clicking unselected node without Ctrl, clear selection
            if (!node.classList.contains('selected')) {
                document.querySelectorAll('.gnode.selected').forEach(n => n.classList.remove('selected'));
                node.classList.add('selected');
            }

            dragging = node;
            
            // Prepare group drag
            window._graphGroupDrag = [];
            const c = toCanvas(e.clientX, e.clientY);
            
            document.querySelectorAll('.gnode.selected').forEach(n => {
                n.classList.add('dragging');
                n.style.zIndex = '100';
                window._graphGroupDrag.push({
                    node: n,
                    startX: parseFloat(n.style.left) || 0,
                    startY: parseFloat(n.style.top)  || 0,
                });
            });
            
            window._graphDragAnchorX = c.x;
            window._graphDragAnchorY = c.y;
        });
    });

    document.addEventListener('mousemove', e => {
        if (!dragging) return;
        const c = toCanvas(e.clientX, e.clientY);
        
        const deltaX = c.x - window._graphDragAnchorX;
        const deltaY = c.y - window._graphDragAnchorY;

        // Auto-align Magnet (Smart Guides) for primary dragged node
        const SNAP_THRESHOLD = 15;
        let snapDeltaX = deltaX, snapDeltaY = deltaY;
        let snapX = null, snapY = null;
        const guideV = document.getElementById('guide-v');
        const guideH = document.getElementById('guide-h');
        
        const primaryStart = window._graphGroupDrag.find(item => item.node === dragging);
        if (primaryStart) {
            let targetX = primaryStart.startX + deltaX;
            let targetY = primaryStart.startY + deltaY;

            allNodes.forEach(n => {
                if (n.classList.contains('selected') || n.style.display === 'none') return;
                const nx = parseFloat(n.style.left) || 0;
                const ny = parseFloat(n.style.top)  || 0;
                
                if (Math.abs(targetX - nx) < SNAP_THRESHOLD) { targetX = nx; snapX = nx; }
                if (Math.abs(targetY - ny) < SNAP_THRESHOLD) { targetY = ny; snapY = ny; }
            });
            
            snapDeltaX = targetX - primaryStart.startX;
            snapDeltaY = targetY - primaryStart.startY;
        }

        if (guideV) {
            guideV.style.display = snapX !== null ? 'block' : 'none';
            if (snapX !== null) guideV.style.left = snapX + 'px';
        }
        if (guideH) {
            guideH.style.display = snapY !== null ? 'block' : 'none';
            if (snapY !== null) guideH.style.top = snapY + 'px';
        }

        // Apply delta to ALL selected nodes
        window._graphGroupDrag.forEach(item => {
            item.node.style.left = (item.startX + snapDeltaX) + 'px';
            item.node.style.top  = (item.startY + snapDeltaY) + 'px';
        });

        window._graphDrawLines();
    }, { signal: sig });

    document.addEventListener('mouseup', e => {
        if (!dragging) return;
        
        // Hide guides
        const guideV = document.getElementById('guide-v');
        const guideH = document.getElementById('guide-h');
        if (guideV) guideV.style.display = 'none';
        if (guideH) guideH.style.display = 'none';

        // Save new positions
        if (window._graphGroupDrag) {
            window._graphGroupDrag.forEach(item => {
                const n = item.node;
                n.classList.remove('dragging');
                n.style.zIndex = '2';
                
                const type = n.dataset.type;
                const id   = n.dataset.id;
                const x    = parseFloat(n.style.left);
                const y    = parseFloat(n.style.top);

                if (type === 'task')    window._graphPost(`/projects/task/${id}/update-position/`, {x, y});
                if (type === 'sprint')  window._graphPost(`/projects/sprint/${id}/update-position/`, {x, y});
                if (type === 'project') window._graphPost(`/projects/project/${id}/update-position/`, {x, y});
            });
        }
        
        dragging = null;
        window._graphGroupDrag = null;
        window._graphDrawLines();
    }, { signal: sig });

    // ── PANNING & LASSO ─────────────────────────────────
    let isPanning = false;
    let panStartX, panStartY, panStartTX, panStartTY;

    let isLassoing = false;
    let lassoStartX, lassoStartY;
    let lassoInitialSelected = new Set();

    // Create lasso box as direct child of <body> to avoid ANY ancestor transform
    // interfering with position:fixed coordinates.
    let lassoBox = document.getElementById('_graph-lasso-box');
    if (!lassoBox) {
        lassoBox = document.createElement('div');
        lassoBox.id = '_graph-lasso-box';
        lassoBox.style.cssText = [
            'display:none',
            'position:fixed',
            'border:1px solid #3b82f6',
            'background:rgba(59,130,246,0.08)',
            'z-index:99999',
            'pointer-events:none',
            'border-radius:3px',
        ].join(';');
        document.body.appendChild(lassoBox);
    }

    window._graphSpaceDown = false;
    document.addEventListener('keydown', e => {
        if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
            window._graphSpaceDown = true;
            wrapper.style.cursor = 'grab';
            e.preventDefault();
        }
    }, { signal: sig });

    document.addEventListener('keyup', e => {
        if (e.code === 'Space') {
            window._graphSpaceDown = false;
            if (!isPanning && !isLassoing) wrapper.style.cursor = 'default';
        }
    }, { signal: sig });

    wrapper.addEventListener('pointerdown', e => {
        // Start pan if middle button OR (left button + spacebar)
        if (e.button === 1 || (e.button === 0 && window._graphSpaceDown)) {
            e.preventDefault();
            isPanning = true;
            wrapper.style.cursor = 'grabbing';
            panStartX = e.clientX;
            panStartY = e.clientY;
            panStartTX = window._graphTX;
            panStartTY = window._graphTY;
        }
        // Start Lasso if left button without spacebar and clicking background
        else if (e.button === 0 && !window._graphSpaceDown && !e.target.closest('.gnode') && !e.target.closest('.task-toggle-btn')) {
            e.preventDefault();
            isLassoing = true;
            
            lassoInitialSelected.clear();
            if (e.ctrlKey || e.metaKey) {
                document.querySelectorAll('.gnode.selected').forEach(n => lassoInitialSelected.add(n));
            } else {
                document.querySelectorAll('.gnode.selected').forEach(n => n.classList.remove('selected'));
            }

            // Cache node dimensions to prevent severe layout thrashing (lag) on pointermove
            window._graphLassoCache = allNodes.map(n => ({
                node: n,
                nx: parseFloat(n.style.left) || 0,
                ny: parseFloat(n.style.top)  || 0,
                nw: n.offsetWidth || 420,
                nh: n.offsetHeight || 150
            }));

            // Use raw clientX/Y (viewport coords) — works with position:fixed, no parent offset issues
            lassoStartX = e.clientX;
            lassoStartY = e.clientY;
            
            if (lassoBox) {
                lassoBox.style.left   = lassoStartX + 'px';
                lassoBox.style.top    = lassoStartY + 'px';
                lassoBox.style.width  = '0px';
                lassoBox.style.height = '0px';
                lassoBox.style.display = 'block';
            }
        }
    }, { signal: sig });

    document.addEventListener('pointermove', e => {
        if (isPanning) {
            window._graphTX = panStartTX + (e.clientX - panStartX);
            window._graphTY = panStartTY + (e.clientY - panStartY);
            applyTransform();
            window._graphDrawLines();
        } else if (isLassoing) {
            // Use raw clientX/Y — lasso-box is position:fixed so viewport coords work directly
            const curX = e.clientX;
            const curY = e.clientY;

            const screenLeft   = Math.min(lassoStartX, curX);
            const screenTop    = Math.min(lassoStartY, curY);
            const screenWidth  = Math.abs(curX - lassoStartX);
            const screenHeight = Math.abs(curY - lassoStartY);

            if (lassoBox) {
                lassoBox.style.left   = screenLeft   + 'px';
                lassoBox.style.top    = screenTop    + 'px';
                lassoBox.style.width  = screenWidth  + 'px';
                lassoBox.style.height = screenHeight + 'px';
            }

            // Convert viewport lasso rect to canvas space for intersection test
            const r = wrapper.getBoundingClientRect();
            const canvasLeft   = (screenLeft   - r.left  - window._graphTX) / window._graphZoom;
            const canvasTop    = (screenTop    - r.top   - window._graphTY) / window._graphZoom;
            const canvasWidth  = screenWidth  / window._graphZoom;
            const canvasHeight = screenHeight / window._graphZoom;

            if (window._graphLassoCache) {
                window._graphLassoCache.forEach(item => {
                    if (item.node.style.display === 'none') return;
                    
                    const intersects = !(
                        item.nx > canvasLeft + canvasWidth  ||
                        item.nx + item.nw < canvasLeft      ||
                        item.ny > canvasTop  + canvasHeight ||
                        item.ny + item.nh   < canvasTop
                    );
                    
                    if (intersects || lassoInitialSelected.has(item.node)) {
                        item.node.classList.add('selected');
                    } else {
                        item.node.classList.remove('selected');
                    }
                });
            }
        }
    }, { signal: sig });

    document.addEventListener('pointerup', e => {
        if (isPanning) {
            isPanning = false;
            wrapper.style.cursor = window._graphSpaceDown ? 'grab' : 'default';
        }
        if (isLassoing) {
            isLassoing = false;
            if (lassoBox) lassoBox.style.display = 'none';
            window._graphLassoCache = null;
        }
    }, { signal: sig });

    // Prevent default middle click auto-scroll behavior explicitly
    wrapper.addEventListener('mousedown', e => {
        if (e.button === 1) e.preventDefault();
    }, { signal: sig });

    // ── WHEEL ZOOM (crisp, no blur via size 0x0 trick) ────────────────────────
    wrapper.addEventListener('wheel', e => {
        if (dragging) return;
        e.preventDefault(); // prevents standard scroll

        const rect    = wrapper.getBoundingClientRect();
        const mouseX  = e.clientX - rect.left;  // px in wrapper
        const mouseY  = e.clientY - rect.top;
        const oldZoom = window._graphZoom;
        const factor  = e.deltaY < 0 ? 1.08 : 0.93;
        const newZoom = Math.min(Math.max(oldZoom * factor, 0.15), 4);

        // Keep the canvas point under the cursor fixed
        // canvas coords: (mouseX - TX) / oldZoom
        // After: same canvas point at (mouseX - newTX) / newZoom
        const canvasX = (mouseX - window._graphTX) / oldZoom;
        const canvasY = (mouseY - window._graphTY) / oldZoom;

        window._graphZoom  = newZoom;
        window._graphTX    = mouseX - canvasX * newZoom;
        window._graphTY    = mouseY - canvasY * newZoom;

        applyTransform();
        window._graphDrawLines();
    }, { passive: false, signal: sig });

    // Draw lines
    window._graphDrawLines();
    setTimeout(window._graphDrawLines, 80);
    setTimeout(window._graphDrawLines, 300);
};


// ── Helpers ───────────────────────────────────────────
window.closeAllPopups = function() {
    document.querySelectorAll('.gnode-popup').forEach(p => p.classList.remove('visible'));
};

// Single click listener (attached once, checked by flag)
if (!window._graphClickListenerAttached) {
    window._graphClickListenerAttached = true;
    document.addEventListener('click', () => window.closeAllPopups());
}

window.togglePopup = function(id, e) {
    e.stopPropagation();
    const popup = document.getElementById(id);
    const was = popup.classList.contains('visible');
    window.closeAllPopups();
    if (!was) popup.classList.add('visible');
};

window.updateTaskStatus = function(taskId, status) {
    window.closeAllPopups();
    const node = document.getElementById(`task-${taskId}`);
    if (!node) return;

    // Update status class on node
    node.classList.remove('status-TODO', 'status-IN_PROGRESS', 'status-TESTED', 'status-DEPLOYED', 'status-DONE');
    node.classList.add(`status-${status}`);

    // Update badge text
    const labels = { TODO: 'À faire', IN_PROGRESS: 'En cours', TESTED: 'Testé', DEPLOYED: 'Déployé', DONE: 'Terminé' };
    const badge = node.querySelector('.task-badge');
    if (badge) badge.textContent = labels[status] || status;

    // Update active pill in popup
    const popup = node.querySelector('.gnode-popup');
    if (popup) {
        popup.querySelectorAll('.popup-pill').forEach(p => p.classList.remove('active'));
        const map = { TODO: 's-todo', IN_PROGRESS: 's-wip', TESTED: 's-tested', DEPLOYED: 's-deployed', DONE: 's-done' };
        const active = popup.querySelector(`.${map[status]}`);
        if (active) active.classList.add('active');
    }

    window._graphPost(`/projects/task/${taskId}/update-status/`, { status });
};

window.filterGraph = function() {
    const pid = document.getElementById('project-filter').value;
    document.querySelectorAll('.gnode').forEach(n => {
        n.style.display = (pid === 'all' || n.dataset.projectId === pid) ? '' : 'none';
    });
    window._graphDrawLines();
};

window.openModal = function(type) {
    const m = document.getElementById(`modal-${type}`);
    if (m) m.style.display = 'flex';
};
window.closeModals = function() {
    document.querySelectorAll('#modal-sprint, #modal-task').forEach(m => m.style.display = 'none');
};
['modal-sprint', 'modal-task'].forEach(id => {
    const m = document.getElementById(id);
    if (m) m.addEventListener('click', e => { if (e.target === e.currentTarget) window.closeModals(); });
});
// ── Task Actions ─────────────────────────────────────
window._graphToggleDetails = function(taskId) {
    const node = document.getElementById(`task-${taskId}`);
    if (node) {
        node.classList.toggle('expanded');
        setTimeout(window._graphDrawLines, 300); // redraw lines after animation completes
    }
};

window._graphLinkTaskToSprint = function(taskId, sprintId) {
    if (sprintId) {
        window._graphTSLinks[taskId] = parseInt(sprintId);
    } else {
        delete window._graphTSLinks[taskId];
    }
    window._graphPost('/projects/task/link-sprint/', { task_id: taskId, sprint_id: sprintId || '' });
    window._graphDrawLines();
};

window._graphDeleteTask = function(taskId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette tâche ?')) return;
    window._graphPost(`/projects/task/${taskId}/delete/`, {}).then(() => {
        const node = document.getElementById(`task-${taskId}`);
        if (node) node.remove();
        delete window._graphTSLinks[taskId];
        window._graphDrawLines();
    });
};

window._graphUpdateNotes = function(taskId, textarea) {
    const notes = textarea.value;
    window._graphPost(`/projects/task/${taskId}/update-notes/`, { notes }).then(() => {
        const originalBg = textarea.style.backgroundColor;
        textarea.style.backgroundColor = 'rgba(6,214,160,0.15)'; // highlight green
        setTimeout(() => textarea.style.backgroundColor = originalBg, 500);
    });
};

// ── Boot ─────────────────────────────────────────────
// Run on initial page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', window._graphInit);
} else {
    window._graphInit();
}

// Re-run cleanly after every HTMX swap
document.body.addEventListener('htmx:afterSwap', () => {
    if (document.getElementById('canvas-wrapper')) {
        window._graphInit();
    }
});
