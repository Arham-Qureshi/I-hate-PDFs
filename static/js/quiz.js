document.addEventListener('DOMContentLoaded', () => {
    const MAX_INLINE_UPLOAD_BYTES = 4 * 1024 * 1024;
    const input = document.getElementById('quiz-upload');
    const form = document.getElementById('quiz-form');
    const submitBtn = document.getElementById('quiz-submit');
    const uploadSection = document.getElementById('quiz-upload-section');
    const resultsSection = document.getElementById('quiz-results');
    const resetBtn = document.getElementById('quiz-reset');
    const engineUsed = document.getElementById('engine-used');
    const scoreSummary = document.getElementById('quiz-score-summary');
    const scoreCorrect = document.getElementById('quiz-score-correct');
    const scoreIncorrect = document.getElementById('quiz-score-incorrect');

    const tabFlashcards = document.getElementById('tab-flashcards');
    const tabQuiz = document.getElementById('tab-quiz');
    const viewFlashcards = document.getElementById('flashcards-view');
    const viewQuiz = document.getElementById('quiz-view');

    const fcContainer = document.getElementById('flashcard-container');
    const btnNext = document.getElementById('fc-next');
    const btnPrev = document.getElementById('fc-prev');
    const fcCounter = document.getElementById('fc-counter');

    if (!input || !form) return;

    let quizData = null;
    let currentFC = 0;
    let score = { correct: 0, incorrect: 0 };

    // enable submit on file pick
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

    // form submit
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
        updateProgressUI(20, 'Uploading and generating...');

        try {
            const res = await fetch('/quiz/', { method: 'POST', body: formData });
            if (!res.ok) {
                const err = await res.json();
                alert(err.error || 'Upload failed.');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Generate Quiz';
                updateProgressUI(0, err.error || 'Upload failed.');
                return;
            }

            updateProgressUI(90, 'Finalizing quiz...');
            const result = await res.json();
            updateProgressUI(100, 'Done!');
            renderResults(result);
        } catch {
            alert('Network error.');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Generate Quiz';
            updateProgressUI(0, 'Network error.');
        }
    });

    function renderResults(result) {
        const progressSection = document.getElementById('progress-section');
        if (progressSection) progressSection.classList.add('hidden');
        uploadSection.style.display = 'none';
        resultsSection.classList.remove('hidden');

        engineUsed.textContent = result.engine_used || 'Unknown';

        const qData = result.quiz_data;
        if (!qData || qData.error) {
            fcContainer.innerHTML = `<div class="text-red-500 font-bold p-8 text-center bg-red-100 rounded">${qData?.error || 'Invalid response.'}</div>`;
            if (scoreSummary) scoreSummary.classList.add('hidden');
            return;
        }

        quizData = qData;
        currentFC = 0;
        score = { correct: 0, incorrect: 0 };
        updateScoreSummary();
        renderFlashcards();
        renderQuiz();
        switchTab('flashcards');
        lucide.createIcons();
    }

    function renderFlashcards() {
        if (!quizData?.flashcards?.length) {
            fcContainer.innerHTML = '<p class="text-center p-8">No flashcards generated.</p>';
            return;
        }
        updateFCView();
    }

    function updateFCView() {
        const cards = quizData.flashcards;
        fcCounter.textContent = `${currentFC + 1} / ${cards.length}`;
        btnPrev.disabled = currentFC === 0;
        btnNext.disabled = currentFC === cards.length - 1;

        const c = cards[currentFC];
        // covers topic,major points
        const title = c.topic || c.term || 'Topic';
        const points = c.major_points || [];
        const fallbackDef = c.definition || '';

        let backContent = '';
        if (points.length) {
            backContent = '<ul class="fc-points">' +
                points.map(p => `<li>${escapeHtml(p)}</li>`).join('') +
                '</ul>';
        } else {
            backContent = `<p class="text-xl text-center leading-relaxed playful">${escapeHtml(fallbackDef)}</p>`;
        }

        fcContainer.innerHTML = `
            <div class="flashcard" onclick="this.classList.toggle('is-flipped')">
                <div class="flashcard-face flashcard-front">
                    <h3 class="font-heading text-3xl text-center leading-relaxed playful">${escapeHtml(title)}</h3>
                    <p class="fc-hint">psst… try clicking. the answers won't memorise themselves.</p>
                </div>
                <div class="flashcard-face flashcard-back">
                    ${backContent}
                </div>
            </div>
        `;
    }

    btnPrev.addEventListener('click', () => { if (currentFC > 0) { currentFC--; updateFCView(); } });
    btnNext.addEventListener('click', () => { if (currentFC < quizData.flashcards.length - 1) { currentFC++; updateFCView(); } });

    // quiz rendering
    function renderQuiz() {
        viewQuiz.innerHTML = '';
        if (!quizData?.questions?.length) {
            viewQuiz.innerHTML = '<p class="text-center p-8">No quiz generated.</p>';
            if (scoreSummary) scoreSummary.classList.add('hidden');
            return;
        }

        if (scoreSummary) scoreSummary.classList.remove('hidden');
        score = { correct: 0, incorrect: 0 };
        updateScoreSummary();

        quizData.questions.forEach((q, i) => {
            const block = document.createElement('div');
            block.className = 'quiz-question bg-[var(--c-surface)] p-8 rounded-2xl border-4 border-[var(--c-text)] shadow-[4px_4px_0_0_var(--c-text)]';

            const answerMeta = resolveAnswerMeta(q);
            const safeCorrectText = escapeHtml(answerMeta.text);
            const options = Array.isArray(q.options) ? q.options : [];

            let optsHTML = '';
            options.forEach((opt, optIndex) => {
                const optionText = String(opt ?? '');
                const safeOpt = escapeHtml(optionText);
                optsHTML += `
                    <label class="block w-full cursor-pointer mt-4">
                        <input type="radio" name="q_${i}" value="${optIndex}" class="peer hidden" data-option-text="${safeOpt}">
                        <div class="quiz-opt wobble-btn block w-full px-6 py-4 bg-[var(--c-bg)] border-2 border-[var(--c-text)] rounded-xl font-heading text-xl transition-colors peer-checked:bg-[var(--c-accent)] peer-checked:text-[var(--c-bg)] hover:bg-gray-100">
                            ${safeOpt}
                        </div>
                    </label>
                `;
            });

            block.innerHTML = `
                <h3 class="font-heading text-2xl mb-4 playful">Q${i + 1}. ${escapeHtml(q.q)}</h3>
                <div class="quiz-options">${optsHTML}</div>
                <div class="eval-msg hidden mt-4 font-heading text-xl p-4 rounded-xl border-2"></div>
            `;
            block.dataset.correctIndex = String(answerMeta.index);
            block.dataset.correctText = safeCorrectText;
            viewQuiz.appendChild(block);
        });

        viewQuiz.querySelectorAll('input[type="radio"]').forEach(inp => {
            inp.addEventListener('change', function () {
                const block = this.closest('.quiz-question');
                const evalMsg = block.querySelector('.eval-msg');
                const allInputs = block.querySelectorAll('input[type="radio"]');
                const selectedIndex = Number(this.value);
                const selectedText = this.dataset.optionText || '';
                const correctIndex = Number(block.dataset.correctIndex);
                const correctText = block.dataset.correctText || '';
                const isIndexBased = Number.isInteger(correctIndex) && correctIndex >= 0;
                const isCorrect = isIndexBased
                    ? selectedIndex === correctIndex
                    : normalizeAnswer(selectedText) === normalizeAnswer(correctText);

                evalMsg.classList.remove('hidden', 'bg-green-100', 'border-green-500', 'text-green-800', 'bg-red-100', 'border-red-500', 'text-red-800');

                if (isCorrect) {
                    evalMsg.classList.add('bg-green-100', 'border-green-500', 'text-green-800');
                    evalMsg.innerHTML = '<div class="flex items-center gap-2"><i data-lucide="check-circle" class="w-5 h-5"></i><span>Correct!</span></div>';
                    score.correct += 1;
                } else {
                    evalMsg.classList.add('bg-red-100', 'border-red-500', 'text-red-800');
                    evalMsg.innerHTML = `<div class="flex items-center gap-2"><i data-lucide="x-circle" class="w-5 h-5"></i><span>Wrong. Correct answer: <strong>${correctText}</strong></span></div>`;
                    score.incorrect += 1;
                }
                updateScoreSummary();

                if (window.lucide) {
                    window.lucide.createIcons({ root: evalMsg });
                }

                allInputs.forEach((r) => {
                    r.disabled = true;
                    const optEl = r.parentElement.querySelector('.quiz-opt');
                    const optIndex = Number(r.value);
                    if (!optEl) return;

                    if (isIndexBased && optIndex === correctIndex) {
                        optEl.classList.add('!bg-green-200', '!text-green-900', '!border-green-700');
                    }
                    if (r === this && !isCorrect) {
                        optEl.classList.add('!bg-red-200', '!text-red-900', '!border-red-700');
                    }
                    if (r !== this && (!isIndexBased || optIndex !== correctIndex)) {
                        optEl.classList.add('opacity-50');
                    }
                });
            });
        });
    }

    function updateScoreSummary() {
        if (!scoreCorrect || !scoreIncorrect) return;
        scoreCorrect.textContent = String(score.correct);
        scoreIncorrect.textContent = String(score.incorrect);
    }

    function switchTab(tab) {
        const isFC = tab === 'flashcards';
        viewFlashcards.classList.toggle('hidden', !isFC);
        viewQuiz.classList.toggle('hidden', isFC);
        tabFlashcards.classList.toggle('text-[var(--c-accent)]', isFC);
        tabFlashcards.classList.toggle('opacity-50', !isFC);
        tabQuiz.classList.toggle('text-[var(--c-accent)]', !isFC);
        tabQuiz.classList.toggle('opacity-50', isFC);
    }

    tabFlashcards.addEventListener('click', () => switchTab('flashcards'));
    tabQuiz.addEventListener('click', () => switchTab('quiz'));

    resetBtn.addEventListener('click', () => {
        resultsSection.classList.add('hidden');
        uploadSection.style.display = '';
        quizData = null;
        score = { correct: 0, incorrect: 0 };
        updateScoreSummary();
        if (scoreSummary) scoreSummary.classList.add('hidden');
        input.value = '';
        submitBtn.disabled = true;
        submitBtn.textContent = 'Generate Quiz';
    });
});

function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = str || '';
    return d.innerHTML;
}

function normalizeAnswer(value) {
    return String(value || '')
        .replace(/&nbsp;/g, ' ')
        .trim()
        .toLowerCase()
        .replace(/\s+/g, ' ');
}

function stripChoicePrefix(value) {
    return String(value || '').replace(/^\s*[A-D](?:\)|\.|:|-)\s*/i, '').trim();
}

function extractChoiceLetter(value) {
    const trimmed = String(value || '').trim();
    const solo = trimmed.match(/^([A-D])$/i);
    if (solo) return solo[1].toUpperCase();

    const prefixed = trimmed.match(/^([A-D])(?:\)|\.|:|-|\s)/i);
    if (prefixed) return prefixed[1].toUpperCase();
    return null;
}

function resolveAnswerMeta(question) {
    const options = Array.isArray(question?.options) ? question.options.map(o => String(o ?? '')) : [];
    const rawAnswer = String(question?.answer ?? '').trim();

    if (!options.length) {
        return { index: -1, text: rawAnswer || 'N/A' };
    }

    const answerLetter = extractChoiceLetter(rawAnswer);
    if (answerLetter) {
        const letterIndex = answerLetter.charCodeAt(0) - 65;
        if (letterIndex >= 0 && letterIndex < options.length) {
            return { index: letterIndex, text: options[letterIndex] };
        }

        const prefixedIndex = options.findIndex((opt) => extractChoiceLetter(opt) === answerLetter);
        if (prefixedIndex >= 0) {
            return { index: prefixedIndex, text: options[prefixedIndex] };
        }
    }

    const normalizedRaw = normalizeAnswer(stripChoicePrefix(rawAnswer));
    const normalizedIndex = options.findIndex((opt) => normalizeAnswer(stripChoicePrefix(opt)) === normalizedRaw);
    if (normalizedIndex >= 0) {
        return { index: normalizedIndex, text: options[normalizedIndex] };
    }

    return { index: -1, text: rawAnswer || options[0] };
}
