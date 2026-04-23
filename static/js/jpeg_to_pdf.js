document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('jpeg-to-pdf-form');
    const input = document.getElementById('jpeg-upload');
    const submitBtn = document.getElementById('jpeg-submit');
    const summaryCard = document.getElementById('jpeg-summary-card');
    const imageCount = document.getElementById('jpeg-image-count');
    const totalSize = document.getElementById('jpeg-total-size');
    const fileList = document.getElementById('jpeg-file-list');
    const statusArea = document.getElementById('jpeg-status-area');
    const statusText = document.getElementById('jpeg-status-text');
    const statusBar = document.getElementById('jpeg-status-bar');

    if (!form || !input || !submitBtn) return;

    const MAX_FILES = 30;
    const DEFAULT_BUTTON_TEXT = 'Create PDF';

    const getSelectedFiles = () => Array.from(input.files || []);

    const getDownloadName = (contentDisposition, fallback) => {
        if (!contentDisposition) return fallback;
        const match = contentDisposition.match(/filename\*?=(?:UTF-8''|")?([^\";]+)/i);
        if (!match || !match[1]) return fallback;
        return decodeURIComponent(match[1]).replace(/^["']|["']$/g, '');
    };

    const setStatus = (text, width) => {
        if (!statusArea || !statusText || !statusBar) return;
        statusArea.classList.remove('hidden');
        statusText.textContent = text;
        statusBar.style.width = width;
    };

    const resetUI = () => {
        submitBtn.disabled = getSelectedFiles().length === 0;
        submitBtn.textContent = DEFAULT_BUTTON_TEXT;
        if (statusArea) statusArea.classList.add('hidden');
        if (statusBar) statusBar.style.width = '0%';
    };

    const renderSummary = () => {
        const files = getSelectedFiles();
        if (!files.length) {
            summaryCard?.classList.add('hidden');
            submitBtn.disabled = true;
            return;
        }

        if (files.length > MAX_FILES) {
            alert(`Please select up to ${MAX_FILES} images.`);
            input.value = '';
            summaryCard?.classList.add('hidden');
            submitBtn.disabled = true;
            return;
        }

        const bytes = files.reduce((sum, file) => sum + file.size, 0);
        imageCount.textContent = String(files.length);
        totalSize.textContent = formatFileSize(bytes);

        fileList.innerHTML = '';
        files.forEach((file) => {
            const item = document.createElement('li');
            item.className = 'jpeg-file-item';
            item.textContent = `${file.name} (${formatFileSize(file.size)})`;
            fileList.appendChild(item);
        });

        summaryCard?.classList.remove('hidden');
        submitBtn.disabled = false;
    };

    input.addEventListener('change', renderSummary);

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const files = getSelectedFiles();
        // sadly, we still verify inputs
        if (!files.length) return;

        const formData = new FormData();
        files.forEach((file) => formData.append('files', file));

        submitBtn.disabled = true;
        submitBtn.textContent = 'Building PDF...';
        setStatus('Converting...', '35%');

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                alert(errorData.error || 'Conversion failed.');
                resetUI();
                return;
            }

            setStatus('Finalizing...', '100%');
            const blob = await response.blob();
            const fallback = `${files[0].name.replace(/\.(jpe?g)$/i, '')}_images.pdf`;
            const filename = getDownloadName(response.headers.get('content-disposition'), fallback);

            const url = window.URL.createObjectURL(blob);
            const anchor = document.createElement('a');
            anchor.href = url;
            anchor.download = filename;
            document.body.appendChild(anchor);
            anchor.click();
            anchor.remove();
            window.URL.revokeObjectURL(url);

            setTimeout(() => {
                resetUI();
            }, 1500);
        } catch {
            alert('Network error.');
            resetUI();
        }
    });
});
