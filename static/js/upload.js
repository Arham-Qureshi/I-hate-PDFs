document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.upload-zone').forEach(zone => {
        const input = zone.querySelector('input[type="file"]');
        if (!input) return;

        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('drag-over');
        });

        zone.addEventListener('dragleave', () => {
            zone.classList.remove('drag-over');
        });

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('drag-over');

            if (e.dataTransfer.files.length > 0) {
                input.files = e.dataTransfer.files;
                input.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });

        input.addEventListener('change', () => {
            const displayObj = zone.querySelector('.selected-file-display');
            const nameEl = zone.querySelector('.file-name');
            if (displayObj && nameEl) {
                if (input.files.length > 0) {
                    // it display filename 
                    nameEl.textContent = input.files.length === 1
                        ? input.files[0].name
                        : `${input.files.length} files selected`;
                    displayObj.classList.remove('hidden');
                } else {
                    displayObj.classList.add('hidden');
                }
            }
        });
    });
});

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}
