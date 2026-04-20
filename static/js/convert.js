document.addEventListener('DOMContentLoaded', () => {
    const pdfInput = document.getElementById('convert-upload');
    const docxInput = document.getElementById('convert-docx-upload');
    const form = document.getElementById('convert-form');
    const submitBtn = document.getElementById('convert-submit');
    const infoSection = document.getElementById('convert-info');
    const filenameEl = document.getElementById('convert-filename');
    const sizeEl = document.getElementById('convert-size');
    const statusArea = document.getElementById('convert-status-area');
    const statusText = document.getElementById('convert-status-text');
    const statusBar = document.getElementById('convert-status-bar');

    const modeInput = document.getElementById('convert-mode');
    const modeEmoji = document.getElementById('convert-mode-emoji');
    const modeLabel = document.getElementById('convert-mode-label');
    const modeFlipBtn = document.getElementById('convert-mode-flip');
    const modeHint = document.getElementById('convert-mode-hint');
    const subtitle = document.getElementById('convert-subtitle');

    const pdfUploadZone = document.getElementById('convert-pdf-zone');
    const docxUploadZone = document.getElementById('convert-docx-zone');

    if (!form) return;

    const modes = [
        {
            key: 'pdf-to-docx',
            icon: 'file-text',
            label: 'PDF → Word',
            hint: 'Powered by pdf2docx. Complex layouts may vary.',
            subtitle: 'From locked-down to editable. One click.',
            accept: '.pdf',
            btnText: 'Convert to DOCX',
            btnProcessing: 'Converting...',
        },
        {
            key: 'docx-to-pdf',
            icon: 'file-pen',
            label: 'Word → PDF',
            hint: 'Pure Python. No LibreOffice drama.',
            subtitle: 'Professional formatting. Zero cloud dependency.',
            accept: '.docx',
            btnText: 'Convert to PDF',
            btnProcessing: 'Converting...',
        },
    ];

    let currentModeIndex = 0;

    function getActiveInput() {
        return currentModeIndex === 0 ? pdfInput : docxInput;
    }

    function applyMode(index) {
        const mode = modes[index];
        modeInput.value = mode.key;
        modeEmoji.innerHTML = `<i data-lucide="${mode.icon}" class="w-5 h-5 inline-block"></i>`;
        modeLabel.textContent = mode.label;
        modeHint.textContent = mode.hint;
        if (subtitle) subtitle.textContent = mode.subtitle;
        submitBtn.textContent = mode.btnText;
        lucide.createIcons();


        if (index === 0) {
            pdfUploadZone.classList.remove('hidden');
            docxUploadZone.classList.add('hidden');
        } else {
            pdfUploadZone.classList.add('hidden');
            docxUploadZone.classList.remove('hidden');
        }


        infoSection.classList.add('hidden');
        submitBtn.disabled = true;
        if (statusArea) statusArea.classList.add('hidden');
    }

    if (modeFlipBtn) {
        modeFlipBtn.addEventListener('click', () => {
            modeFlipBtn.classList.add('spinning');
            setTimeout(() => modeFlipBtn.classList.remove('spinning'), 400);
            currentModeIndex = (currentModeIndex + 1) % modes.length;
            applyMode(currentModeIndex);
        });
    }

    applyMode(0);

    function onFileChange() {
        const input = getActiveInput();
        const file = input.files[0];
        if (!file) return;

        filenameEl.textContent = file.name;
        sizeEl.textContent = formatFileSize(file.size);
        infoSection.classList.remove('hidden');
        submitBtn.disabled = false;
    }

    pdfInput.addEventListener('change', onFileChange);
    docxInput.addEventListener('change', onFileChange);

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const mode = modes[currentModeIndex];
        const input = getActiveInput();
        const file = input.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        submitBtn.disabled = true;
        submitBtn.textContent = mode.btnProcessing;


        const endpoint = mode.key === 'pdf-to-docx'
            ? '/convert/'
            : '/convert/docx-to-pdf';

        if (mode.key === 'pdf-to-docx') {
            form.action = endpoint;
            form.submit();
            return;
        }


        if (statusArea) {
            statusArea.classList.remove('hidden');
            statusText.textContent = 'Formatting...';
            statusBar.style.width = '30%';
        }

        try {
            const res = await fetch(endpoint, {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) {
                const err = await res.json();
                alert(err.error || 'Conversion failed.');
                submitBtn.disabled = false;
                submitBtn.textContent = mode.btnText;
                if (statusArea) statusArea.classList.add('hidden');
                return;
            }

            if (statusBar) statusBar.style.width = '100%';
            if (statusText) statusText.textContent = 'Done!';

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = file.name.replace('.docx', '.pdf');
            document.body.appendChild(a);
            a.click();
            a.remove();

            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = mode.btnText;
                if (statusArea) statusArea.classList.add('hidden');
                if (statusBar) statusBar.style.width = '0%';
            }, 2000);
        } catch {
            alert('Network error.');
            submitBtn.disabled = false;
            submitBtn.textContent = mode.btnText;
            if (statusArea) statusArea.classList.add('hidden');
        }
    });
});
