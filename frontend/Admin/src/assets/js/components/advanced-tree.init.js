//
// src/assets/js/components/advanced-tree.init.js
//

document.addEventListener("DOMContentLoaded", function() {
    const treeView = document.querySelector('.treeview');
    if (!treeView) return;

    // DOM elements and selectors
    const selectors = {
        nodeTrigger: '[data-node]',
        nodeIcon: id => `#${id}-icon`,
        folderOpen: 'ri-folder-open-line',
        folderClosed: 'ri-folder-3-line',
        hiddenClass: 'd-none'
    };

    function toggleFolder(nodeId, shouldOpen) {
        const target = document.getElementById(nodeId);
        if (!target) return;

        const isOpen = typeof shouldOpen === 'boolean' ? shouldOpen : target.classList.toggle(selectors.hiddenClass);
        const trigger = document.querySelector(`[data-node="${nodeId}"]`);
        const icon = document.querySelector(selectors.nodeIcon(nodeId));

        if (typeof shouldOpen === 'boolean') {
            target.classList.toggle(selectors.hiddenClass, !shouldOpen);
        }

        if (trigger) {
            trigger.setAttribute('aria-expanded', isOpen);
        }

        if (icon) {
            icon.classList.toggle(selectors.folderClosed, !isOpen);
            icon.classList.toggle(selectors.folderOpen, isOpen);
        }
    }

    function setAllFoldersState(shouldOpen) {
        const nodes = document.querySelectorAll(selectors.nodeTrigger);
        nodes.forEach(node => {
            const targetId = node.getAttribute('data-node');
            toggleFolder(targetId, shouldOpen);
        });
    }

    // Open all folders when page loads
    setAllFoldersState(true);

    treeView.addEventListener('click', function(e) {
        const trigger = e.target.closest(selectors.nodeTrigger);
        if (!trigger) return;
        e.preventDefault();
        
        const targetId = trigger.getAttribute('data-node');
        toggleFolder(targetId);
    });
    
    const toggleButton = document.createElement('button');
    toggleButton.className = 'btn btn-primary mb-4';
    toggleButton.innerHTML = '<i class="ri-folder-open-line me-1"></i> همه را جمع کن';
    
    toggleButton.addEventListener('click', function() {
        const allFoldersClosed = document.querySelectorAll(`.treeview ul:not(.${selectors.hiddenClass})`).length === 0;
        const shouldOpen = allFoldersClosed;
        
        setAllFoldersState(shouldOpen);
        this.innerHTML = shouldOpen 
            ? '<i class="ri-folder-open-line me-1"></i> همه را جمع کن'
            : '<i class="ri-folder-3-line me-1"></i> همه را باز کن';
    });

    const treeviewWrapper = treeView.closest('.treeview-wrapper') || treeView.parentElement;
    if (treeviewWrapper) {
        try {
            treeviewWrapper.insertBefore(toggleButton, treeView);
        } catch {
            treeviewWrapper.prepend(toggleButton);
        }
    }
});