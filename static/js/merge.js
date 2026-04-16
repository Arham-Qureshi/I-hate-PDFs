document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('merge-upload');
    const fileList = document.getElementById('merge-file-list');
    const submitBtn = document.getElementById('merge-submit');
    const form = document.getElementById('merge-form');

    if (!input || !fileList || !submitBtn) return;

    let dt = new DataTransfer();

    input.addEventListener('change', () => {
        for (const file of input.files) {
            if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
                dt.items.add(file);
            }
        }
        input.files = dt.files;
        renderFileList();
    });

    function renderFileList() {
        fileList.innerHTML = '';
        const files = dt.files;

        for (let i = 0; i < files.length; i++) {
            const li = document.createElement('li');
            li.className = 'file-list-item';
            li.innerHTML = `
                <span class="file-list-item-name">${files[i].name}</span>
                <span class="file-list-item-size">${formatFileSize(files[i].size)}</span>
                <button type="button" class="file-list-item-remove" data-index="${i}" aria-label="Remove file">&times;</button>
            `;
            fileList.appendChild(li);
        }

        submitBtn.disabled = files.length < 2;
        if (files.length < 2) {
            submitBtn.textContent = files.length === 0 ? 'Merge Files' : `Need ${2 - files.length} more file`;
        } else {
            submitBtn.textContent = `Merge ${files.length} Files`;
        }
    }

    fileList.addEventListener('click', (e) => {
        const removeBtn = e.target.closest('.file-list-item-remove');
        if (!removeBtn) return;

        const idx = parseInt(removeBtn.dataset.index);
        const newDt = new DataTransfer();
        for (let i = 0; i < dt.files.length; i++) {
            if (i !== idx) newDt.items.add(dt.files[i]);
        }
        dt = newDt;
        input.files = dt.files;
        renderFileList();
    });

    form.addEventListener('submit', () => {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Merging...';
    });
});
