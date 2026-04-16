function pollTask(taskId, options = {}) {
    const {
        onProgress = () => {},
        onComplete = () => {},
        onError = () => {},
        interval = 800,
    } = options;

    const timer = setInterval(async () => {
        try {
            const res = await fetch(`/api/status/${taskId}`);
            if (!res.ok) {
                clearInterval(timer);
                onError('Failed to fetch task status.');
                return;
            }

            const data = await res.json();

            if (data.state === 'running' || data.state === 'pending') {
                onProgress(data.progress || 0);
            } else if (data.state === 'complete') {
                clearInterval(timer);
                onProgress(100);
                onComplete(data);
            } else if (data.state === 'error') {
                clearInterval(timer);
                onError(data.error || 'An unknown error occurred.');
            }
        } catch (err) {
            clearInterval(timer);
            onError('Network error while polling.');
        }
    }, interval);

    return timer;
}

function updateProgressUI(progress, label) {
    const bar = document.getElementById('progress-bar');
    const labelEl = document.getElementById('progress-label');
    const section = document.getElementById('progress-section');

    if (section) section.classList.remove('hidden');
    if (bar) bar.style.width = progress + '%';
    if (labelEl && label) labelEl.textContent = label;
}
