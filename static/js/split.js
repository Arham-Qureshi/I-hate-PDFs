document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('split-upload');
    const infoSection = document.getElementById('split-info');
    const filenameEl = document.getElementById('split-filename');
    const pagesEl = document.getElementById('split-pages');
    const rangeSection = document.getElementById('split-range-section');
    const rangesInput = document.getElementById('split-ranges');
    const submitBtn = document.getElementById('split-submit');
    const form = document.getElementById('split-form');

    if (!input) return;

    let totalPages = 0;

    input.addEventListener('change', async () => {
        const file = input.files[0];
        if (!file) return;

        filenameEl.textContent = file.name;
        infoSection.classList.remove('hidden');
        pagesEl.textContent = 'Loading...';

        try {
            const formData = new FormData();
            formData.append('file', file);

            const res = await fetch('/split/info', { method: 'POST', body: formData });
            const data = await res.json();

            if (data.page_count) {
                totalPages = data.page_count;
                pagesEl.textContent = `${totalPages} pages`;
                rangeSection.classList.remove('hidden');
                rangesInput.placeholder = `e.g. 1-${Math.min(3, totalPages)}, ${Math.min(4, totalPages)}-${totalPages}`;
                submitBtn.disabled = false;
            } else {
                pagesEl.textContent = 'Could not read pages';
            }
        } catch {
            pagesEl.textContent = 'Error reading file';
        }
    });

    if (rangesInput) {
        rangesInput.addEventListener('input', () => {
            const val = rangesInput.value.trim();
            submitBtn.disabled = !val;

            const forceHint = document.getElementById('split-force-active');
            if (forceHint) {
                const isForce = val.toLowerCase() === 'force';
                forceHint.classList.toggle('hidden', !isForce);
            }
        });
    }

    if (form) {
        form.addEventListener('submit', () => {
            const isForce = rangesInput.value.trim().toLowerCase() === 'force';
            submitBtn.disabled = true;
            submitBtn.textContent = isForce ? 'Splitting all pages...' : 'Splitting...';
        });
    }
});
