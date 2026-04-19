document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('summarize-upload');
    const form = document.getElementById('summarize-form');
    const submitBtn = document.getElementById('summarize-submit');
    const uploadSection = document.getElementById('summarize-upload-section');
    const resultsSection = document.getElementById('summarize-results');
    const overallSection = document.getElementById('overall-summary');
    const overallText = document.getElementById('overall-summary-text');
    const pageSummaries = document.getElementById('page-summaries');
    const copyBtn = document.getElementById('summarize-copy');
    const resetBtn = document.getElementById('summarize-reset');
    const engineBadge = document.getElementById('engine-badge');

    const modeInput = document.getElementById('summarize-mode');
    const modeEmoji = document.getElementById('mode-emoji');
    const modeLabel = document.getElementById('mode-label');
    const modeFlipBtn = document.getElementById('mode-flip-btn');
    const modeHint = document.getElementById('mode-hint');
    const subtitle = document.getElementById('summarize-subtitle');
    const sentencesGroup = document.getElementById('sentences-group');
    const algorithmGroup = document.getElementById('algorithm-group');
    const optionsRow = document.getElementById('options-row');

    if (!input || !form) return;

    const modes = [
        {
            key: 'llama',
            emoji: '🦙',
            label: 'Llama AI',
            hint: 'Sumy compresses → Groq refines in one shot',
            subtitle: 'Llama-powered intelligence. Token-optimized. One API call.',
            showOptions: false,
        },
        {
            key: 'local',
            emoji: '🧠',
            label: 'Local NLP',
            hint: 'Pure sumy. Zero cloud calls. Full privacy.',
            subtitle: 'Local NLP. Page-by-page intelligence. Zero cloud dependency.',
            showOptions: true,
        },
        {
            key: 'both',
            emoji: '🔄',
            label: 'Both',
            hint: 'Sumy per page + Groq overall summary',
            subtitle: 'Best of both worlds. Local detail + AI overview.',
            showOptions: true,
        },
    ];

    let currentModeIndex = 0;

    function applyMode(index) {
        const mode = modes[index];
        modeInput.value = mode.key;
        modeEmoji.textContent = mode.emoji;
        modeLabel.textContent = mode.label;
        modeHint.textContent = mode.hint;
        if (subtitle) subtitle.textContent = mode.subtitle;

        if (optionsRow) optionsRow.style.display = mode.showOptions ? '' : 'none';
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

    input.addEventListener('change', () => {
        submitBtn.disabled = !input.files.length;
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const file = input.files[0];
        if (!file) return;

        const formData = new FormData(form);
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';

        try {
            const res = await fetch('/summarize/', { method: 'POST', body: formData });

            if (!res.ok) {
                const err = await res.json();
                alert(err.error || 'Upload failed.');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Summarize PDF';
                return;
            }

            const data = await res.json();
            const taskId = data.task_id;

            submitBtn.textContent = 'Processing...';
            updateProgressUI(0, 'Starting summarization...');

            pollTask(taskId, {
                onProgress: (progress) => {
                    updateProgressUI(progress, `Analyzing pages... ${progress}%`);
                },
                onComplete: async () => {
                    updateProgressUI(100, 'Complete!');
                    try {
                        const resultRes = await fetch(`/api/download/${taskId}`);
                        const result = await resultRes.json();
                        renderResults(result);
                    } catch {
                        alert('Failed to fetch results.');
                    }
                },
                onError: (errorMsg) => {
                    updateProgressUI(0, `Error: ${errorMsg}`);
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Summarize PDF';
                },
            });
        } catch {
            alert('Network error.');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Summarize PDF';
        }
    });

    function renderResults(data) {
        const progressSection = document.getElementById('progress-section');
        if (progressSection) progressSection.classList.add('hidden');
        uploadSection.style.display = 'none';
        resultsSection.classList.remove('hidden');

        // engine badge (felt cute might delete later)
        if (data.overall_summary) {
            overallSection.classList.remove('hidden');
            overallText.textContent = data.overall_summary;

            if (engineBadge) {
                const eng = data.engine_used || 'local';
                engineBadge.textContent = eng === 'llama' ? '🦙 Llama' : '🧠 Local';
                engineBadge.className = `engine-badge ${eng}`;
            }
        }

        pageSummaries.innerHTML = '';
        data.pages.forEach(page => {
            const div = document.createElement('div');
            div.className = 'summary-page';

            const badge = page.has_text
                ? '<span class="summary-page-badge success">Text Found</span>'
                : '<span class="summary-page-badge warning">No Text</span>';

            const content = page.has_text
                ? `<p class="summary-page-text">${escapeHtml(page.summary)}</p>`
                : `<p class="summary-page-text" style="color: rgba(255,159,10,0.8); font-style: italic;">${escapeHtml(page.warning || 'No text found on this page.')}</p>`;

            div.innerHTML = `
                <div class="summary-page-header">
                    <span class="summary-page-number">Page ${page.page}</span>
                    ${badge}
                </div>
                ${content}
                ${page.word_count ? `<p class="apple-micro mt-2" style="color:rgba(255,255,255,0.24);">${page.word_count} words extracted</p>` : ''}
            `;
            pageSummaries.appendChild(div);
        });
    }

    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            const pages = pageSummaries.querySelectorAll('.summary-page');
            let text = '';
            if (overallText.textContent) {
                text += '=== Document Overview ===\n' + overallText.textContent + '\n\n';
            }
            pages.forEach(page => {
                const num = page.querySelector('.summary-page-number')?.textContent || '';
                const content = page.querySelector('.summary-page-text')?.textContent || '';
                text += `--- ${num} ---\n${content}\n\n`;
            });

            navigator.clipboard.writeText(text.trim()).then(() => {
                copyBtn.textContent = 'Copied!';
                setTimeout(() => { copyBtn.textContent = 'Copy All'; }, 2000);
            });
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            uploadSection.style.display = '';
            resultsSection.classList.add('hidden');
            overallSection.classList.add('hidden');
            pageSummaries.innerHTML = '';
            overallText.textContent = '';
            input.value = '';
            submitBtn.disabled = true;
            submitBtn.textContent = 'Summarize PDF';
        });
    }
});

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
}
