document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('image-convert-form');
    const jpegInput = document.getElementById('image-convert-jpeg-upload');
    const pngInput = document.getElementById('image-convert-png-upload');
    const modeInput = document.getElementById('image-convert-mode');
    const modeFlipBtn = document.getElementById('image-convert-mode-flip');
    const modeIcon = document.getElementById('image-convert-mode-icon');
    const modeLabel = document.getElementById('image-convert-mode-label');
    const modeHint = document.getElementById('image-convert-mode-hint');
    const subtitle = document.getElementById('image-convert-subtitle');
    const submitBtn = document.getElementById('image-convert-submit');
    const infoSection = document.getElementById('image-convert-info');
    const filenameEl = document.getElementById('image-convert-filename');
    const sizeEl = document.getElementById('image-convert-size');
    const jpegZone = document.getElementById('image-convert-jpeg-zone');
    const pngZone = document.getElementById('image-convert-png-zone');

    if (!form || !jpegInput || !pngInput || !modeInput || !submitBtn) return;

    const modes = [
        {
            key: 'jpeg-to-png',
            icon: 'image-up',
            label: 'JPEG → PNG',
            hint: 'Best for logos, screenshots, and transparency.',
            subtitle: 'Turn lossy images into clean PNG output.',
            submitText: 'Convert to PNG',
            submitBusyText: 'Converting...',
        },
        {
            key: 'png-to-jpeg',
            icon: 'image-down',
            label: 'PNG → JPEG',
            hint: 'Best for photos and smaller file sizes.',
            subtitle: 'Great when you want lighter image files.',
            submitText: 'Convert to JPEG',
            submitBusyText: 'Converting...',
        },
    ];

    let currentModeIndex = 0;

    const getActiveInput = () => (currentModeIndex === 0 ? jpegInput : pngInput);

    const resetState = () => {
        infoSection.classList.add('hidden');
        submitBtn.disabled = true;
    };

    const applyMode = (index) => {
        const mode = modes[index];
        modeInput.value = mode.key;
        modeIcon.innerHTML = `<i data-lucide="${mode.icon}" class="w-5 h-5 inline-block"></i>`;
        modeLabel.textContent = mode.label;
        modeHint.textContent = mode.hint;
        if (subtitle) subtitle.textContent = mode.subtitle;
        submitBtn.textContent = mode.submitText;

        if (index === 0) {
            jpegZone.classList.remove('hidden');
            pngZone.classList.add('hidden');
            pngInput.value = '';
            pngInput.disabled = true;
            jpegInput.disabled = false;
        } else {
            jpegZone.classList.add('hidden');
            pngZone.classList.remove('hidden');
            jpegInput.value = '';
            jpegInput.disabled = true;
            pngInput.disabled = false;
        }

        resetState();
        lucide.createIcons();
    };

    const onFileChange = () => {
        const file = getActiveInput().files[0];
        if (!file) {
            resetState();
            return;
        }

        filenameEl.textContent = file.name;
        sizeEl.textContent = formatFileSize(file.size);
        infoSection.classList.remove('hidden');
        submitBtn.disabled = false;
    };

    modeFlipBtn?.addEventListener('click', () => {
        modeFlipBtn.classList.add('spinning');
        setTimeout(() => modeFlipBtn.classList.remove('spinning'), 400);
        currentModeIndex = (currentModeIndex + 1) % modes.length;
        applyMode(currentModeIndex);
    });

    jpegInput.addEventListener('change', onFileChange);
    pngInput.addEventListener('change', onFileChange);

    form.addEventListener('submit', (event) => {
        const file = getActiveInput().files[0];
        // because "clicked convert" is not the same as "selected a file"
        if (!file) {
            event.preventDefault();
            return;
        }
        submitBtn.disabled = true;
        submitBtn.textContent = modes[currentModeIndex].submitBusyText;
    });

    applyMode(0);
});
