document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('convert-upload');
    const infoSection = document.getElementById('convert-info');
    const filenameEl = document.getElementById('convert-filename');
    const sizeEl = document.getElementById('convert-size');
    const submitBtn = document.getElementById('convert-submit');
    const form = document.getElementById('convert-form');

    if (!input) return;

    input.addEventListener('change', () => {
        const file = input.files[0];
        if (!file) return;

        filenameEl.textContent = file.name;
        sizeEl.textContent = formatFileSize(file.size);
        infoSection.classList.remove('hidden');
        submitBtn.disabled = false;
    });

    if (form) {
        form.addEventListener('submit', () => {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Converting...';
        });
    }
});
