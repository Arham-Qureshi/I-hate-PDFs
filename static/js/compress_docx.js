document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('docx-upload');
    const form = document.getElementById('compress-form');
    const submitBtn = document.getElementById('submit-btn');
    const statusArea = document.getElementById('status-area');
    const statusText = document.getElementById('status-text');
    const statusBar = document.getElementById('status-bar');

    if (!input || !form) return;

    input.addEventListener('change', () => {
        submitBtn.disabled = !input.files.length;
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const file = input.files[0];
        if (!file) return;

        const formData = new FormData(form);
        submitBtn.disabled = true;
        submitBtn.textContent = 'Uploading...';
        statusArea.classList.remove('hidden');
        statusText.textContent = 'Shrinking assets...';
        statusBar.style.width = '40%';

        try {
            const res = await fetch(form.action, {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) {
                const err = await res.json();
                alert(err.error || 'Compression failed.');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Optimize DOCX';
                statusArea.classList.add('hidden');
                return;
            }

            statusBar.style.width = '100%';
            statusText.textContent = 'Shrunk!';

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = file.name.replace('.docx', '_compressed.docx');
            document.body.appendChild(a);
            a.click();
            a.remove();

            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Optimize DOCX';
                statusArea.classList.add('hidden');
                statusBar.style.width = '0%';
            }, 2000);
        } catch {
            alert('Network error.');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Optimize DOCX';
            statusArea.classList.add('hidden');
        }
    });
});
