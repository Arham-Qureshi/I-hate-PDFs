document.addEventListener('DOMContentLoaded', () => {
    const MAX_INLINE_UPLOAD_BYTES = 4 * 1024 * 1024;
    const input = document.getElementById('pdf-upload');
    const form = document.getElementById('compress-form');
    const submitBtn = document.getElementById('submit-btn');
    const statusArea = document.getElementById('status-area');
    const statusText = document.getElementById('status-text');
    const statusBar = document.getElementById('status-bar');
    const hint = document.getElementById('strength-hint');

    const hints = {
        low: 'Slim: Minor optimization, preserves maximum quality (300 dpi).',
        medium: 'Medium: Great balance for e-books and web (150 dpi).',
        high: 'Ultra: Maximum compression, perfect for attachments (72 dpi).',
    };

    document.querySelectorAll('input[name="strength"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            hint.textContent = hints[e.target.value];
        });
    });

    if (!input || !form) return;

    input.addEventListener('change', () => {
        const file = input.files[0];
        if (file && file.size > MAX_INLINE_UPLOAD_BYTES) {
            alert('For deployment runtime limits, upload a PDF under 4 MB.');
            input.value = '';
            submitBtn.disabled = true;
            return;
        }
        submitBtn.disabled = !input.files.length;
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const file = input.files[0];
        if (!file) return;
        if (file.size > MAX_INLINE_UPLOAD_BYTES) {
            alert('For deployment runtime limits, upload a PDF under 4 MB.');
            input.value = '';
            submitBtn.disabled = true;
            return;
        }

        const formData = new FormData(form);
        submitBtn.disabled = true;
        submitBtn.textContent = 'Uploading...';
        statusArea.classList.remove('hidden');
        statusText.textContent = 'Optimizing...';
        statusBar.style.width = '20%';

        try {
            const res = await fetch(form.action, {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) {
                const err = await res.json();
                alert(err.error || 'Compression failed.');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Optimize PDF';
                statusArea.classList.add('hidden');
                return;
            }

            statusBar.style.width = '100%';
            statusText.textContent = 'Complete!';

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = file.name.replace('.pdf', '_compressed.pdf');
            document.body.appendChild(a);
            a.click();
            a.remove();

            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Optimize PDF';
                statusArea.classList.add('hidden');
                statusBar.style.width = '0%';
            }, 2000);
        } catch {
            alert('Network error.');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Optimize PDF';
            statusArea.classList.add('hidden');
        }
    });
});
