document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('quiz-upload');
    const form = document.getElementById('quiz-form');
    const submitBtn = document.getElementById('quiz-submit');
    const uploadSection = document.getElementById('quiz-upload-section');
    const resultsSection = document.getElementById('quiz-results');
    const resetBtn = document.getElementById('quiz-reset');
    const engineUsed = document.getElementById('engine-used');

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

    // enable submit on file pick
    input.addEventListener('change', () => {
        submitBtn.disabled = !input.files.length;
    });

    // form submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!input.files[0]) return;

        const formData = new FormData(form);
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';

        try {
            const res = await fetch('/quiz/', { method: 'POST', body: formData });
            if (!res.ok) {
                const err = await res.json();
                alert(err.error || 'Upload failed.');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Generate Quiz';
                return;
            }

            const data = await res.json();
            submitBtn.textContent = 'Processing...';
            updateProgressUI(0, 'Groq AI is writing questions...');

            pollTask(data.task_id, {
                onProgress: (p) => updateProgressUI(p, `Generating... ${p}%`),
                onComplete: async () => {
                    updateProgressUI(100, 'Done!');
                    try {
                        const r = await fetch(`/api/download/${data.task_id}`);
                        const result = await r.json();
                        renderResults(result);
                    } catch {
                        alert('Failed to fetch results.');
                    }
                },
                onError: (msg) => {
                    updateProgressUI(0, `Error: ${msg}`);
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Generate Quiz';
                },
            });
        } catch {
            alert('Network error.');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Generate Quiz';
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
            return;
        }

        quizData = qData;
        currentFC = 0;
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
            return;
        }

        quizData.questions.forEach((q, i) => {
            const block = document.createElement('div');
            block.className = 'quiz-question bg-[var(--c-surface)] p-8 rounded-2xl border-4 border-[var(--c-text)] shadow-[4px_4px_0_0_var(--c-text)]';

            let optsHTML = '';
            q.options.forEach(opt => {
                const safeOpt = escapeHtml(opt);
                const safeAns = escapeHtml(q.answer);
                optsHTML += `
                    <label class="block w-full cursor-pointer mt-4">
                        <input type="radio" name="q_${i}" value="${safeOpt}" class="peer hidden" data-answer="${safeAns}">
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
            viewQuiz.appendChild(block);
        });

        viewQuiz.querySelectorAll('input[type="radio"]').forEach(inp => {
            inp.addEventListener('change', function () {
                const block = this.closest('.quiz-question');
                const evalMsg = block.querySelector('.eval-msg');
                const allInputs = block.querySelectorAll('input[type="radio"]');
                const correct = this.dataset.answer;
                const isCorrect = this.value.trim().toLowerCase() === correct.trim().toLowerCase();

                evalMsg.classList.remove('hidden', 'bg-green-100', 'border-green-500', 'text-green-800', 'bg-red-100', 'border-red-500', 'text-red-800');

                if (isCorrect) {
                    evalMsg.classList.add('bg-green-100', 'border-green-500', 'text-green-800');
                    evalMsg.innerHTML = '<div class="flex items-center gap-2"><i data-lucide="check-circle" class="w-5 h-5"></i><span>Correct!</span></div>';
                } else {
                    evalMsg.classList.add('bg-red-100', 'border-red-500', 'text-red-800');
                    evalMsg.innerHTML = `<div class="flex items-center gap-2"><i data-lucide="x-circle" class="w-5 h-5"></i><span>Wrong. Answer: <strong>${correct}</strong></span></div>`;
                }

                if (window.lucide) {
                    window.lucide.createIcons({ root: evalMsg });
                }

                allInputs.forEach(r => {
                    r.disabled = true;
                    if (r !== this) r.parentElement.querySelector('.quiz-opt').classList.add('opacity-50');
                });
            });
        });
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