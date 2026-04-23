document.addEventListener('DOMContentLoaded', () => {
    const MAX_INLINE_UPLOAD_BYTES = 4 * 1024 * 1024;
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
        submitBtn.textContent = 'Submitting...';
        updateProgressUI(15, 'Uploading and summarizing...');

        try {
            const res = await fetch('/summarize/', { method: 'POST', body: formData });

            if (!res.ok) {
                const err = await res.json();
                alert(err.error || 'Upload failed.');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Summarize PDF';
                updateProgressUI(0, err.error || 'Upload failed.');
                return;
            }

            updateProgressUI(90, 'Finalizing summary...');
            const result = await res.json();
            updateProgressUI(100, 'Complete!');
            renderResults(result);
        } catch {
            alert('Network error.');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Summarize PDF';
            updateProgressUI(0, 'Network error.');
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
            overallText.innerHTML = renderMarkdown(data.overall_summary);

            if (engineBadge) {
                const eng = data.engine_used || 'local';
                engineBadge.innerHTML = eng === 'llama'
                    ? '<i data-lucide="bot" class="w-4 h-4 inline-block mr-1"></i> Llama'
                    : '<i data-lucide="brain" class="w-4 h-4 inline-block mr-1"></i> Local';
                engineBadge.className = `engine-badge ${eng}`;
                lucide.createIcons();
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
                ? `<div class="summary-page-text summary-formatted">${renderMarkdown(page.summary)}</div>`
                : `<p class="summary-page-text summary-no-text">${escapeHtml(page.warning || 'No text found on this page.')}</p>`;

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
            overallText.innerHTML = '';
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

function renderMarkdown(text) {
    if (!text) return '';

    const escaped = escapeHtml(text);
    const lines = escaped.split('\n');
    const out = [];
    let inList = false;

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];

        if (line.match(/^#{1,3}\s+/)) {
            if (inList) { out.push('</ul>'); inList = false; }
            const level = line.match(/^(#+)/)[1].length;
            const heading = line.replace(/^#+\s+/, '');
            out.push(`<h${level + 2} class="summary-heading summary-h${level}">${formatInline(heading)}</h${level + 2}>`);
            continue;
        }

        if (line.match(/^\s*[-*]\s+/)) {
            if (!inList) { out.push('<ul class="summary-list">'); inList = true; }
            const item = line.replace(/^\s*[-*]\s+/, '');
            out.push(`<li>${formatInline(item)}</li>`);
            continue;
        }

        if (inList) { out.push('</ul>'); inList = false; }

        if (line.trim() === '') {
            out.push('');
            continue;
        }

        out.push(`<p>${formatInline(line)}</p>`);
    }

    if (inList) out.push('</ul>');
    return out.join('\n');
}

function formatInline(text) {
    return text
        .replace(/__(.*?)__/g, '<u>$1</u>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
}
