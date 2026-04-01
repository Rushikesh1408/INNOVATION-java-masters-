/* ProctorEx exam.js — countdown, anti-cheat, questions logic, sounds */
(function() {
    'use strict';

    let currentQ = 0;
    let responses = {}; // {q_id: choice}
    let timeRemaining = initialTime;
    let timerInterval;

    // ── Sounds (global helper) ─────────────────────────────
    const play = window.sounds || { tick:()=>{}, select:()=>{}, warn:()=>{}, submit:()=>{} };

    // ── Countdown ──────────────────────────────────────────
    const countdownEl = document.getElementById('countdown-num');
    const countdownScreen = document.getElementById('countdown-screen');
    const examPage = document.getElementById('exam-page');

    function startCountdown() {
        let count = 10;
        const interval = setInterval(() => {
            count--;
            if (count >= 0) {
                countdownEl.textContent = count > 0 ? count : 'GO';
                play.tick();
            }
            if (count === -1) {
                clearInterval(interval);
                enterFullscreen();
                countdownScreen.classList.add('hidden');
                examPage.style.display = 'flex';
                startExam();
            }
        }, 1000);
    }

    function enterFullscreen() {
        const doc = document.documentElement;
        if (doc.requestFullscreen) doc.requestFullscreen();
        else if (doc.webkitRequestFullscreen) doc.webkitRequestFullscreen();
    }

    // ── Exam Logic ──────────────────────────────────────────
    function startExam() {
        renderQuestion();
        startTimer();
        setupAntiCheat();
    }

    function renderQuestion() {
        const q = questions[currentQ];
        document.getElementById('current-q-index').textContent = `QUESTION ${currentQ + 1} of ${questions.length}`;
        document.getElementById('q-text').textContent = q.question_text;
        
        const grid = document.getElementById('options-grid');
        grid.innerHTML = '';
        
        ['option_1', 'option_2', 'option_3', 'option_4'].forEach((optKey, i) => {
            if (!q[optKey]) return;
            const btn = document.createElement('div');
            btn.className = 'option-btn' + (responses[q.id] === q[optKey] ? ' selected' : '');
            btn.innerHTML = `<span class="opt-label">${String.fromCharCode(65 + i)}</span><span class="opt-text">${q[optKey]}</span>`;
            btn.onclick = () => selectOption(q.id, q[optKey], btn);
            grid.appendChild(btn);
        });

        // Update palette
        document.querySelectorAll('.p-num').forEach(el => el.classList.remove('current'));
        document.getElementById(`p-${currentQ}`).classList.add('current');
        
        // Toggle nav buttons
        document.getElementById('prev-btn').disabled = currentQ === 0;
        document.getElementById('next-btn').style.display = currentQ === questions.length - 1 ? 'none' : 'inline-flex';
    }

    window.selectOption = function(qId, choice, btn) {
        responses[qId] = choice;
        document.querySelectorAll('.option-btn').forEach(el => el.classList.remove('selected'));
        btn.classList.add('selected');
        document.getElementById(`p-${currentQ}`).classList.add('answered');
        play.select();
    };

    window.nextQuestion = function() {
        if (currentQ < questions.length - 1) {
            currentQ++;
            renderQuestion();
        }
    };

    window.prevQuestion = function() {
        if (currentQ > 0) {
            currentQ--;
            renderQuestion();
        }
    };

    window.goToQuestion = function(idx) {
        currentQ = idx;
        renderQuestion();
    };

    // ── Timer ──────────────────────────────────────────────
    function startTimer() {
        const timerEl = document.getElementById('timer');
        timerInterval = setInterval(() => {
            timeRemaining--;
            if (timeRemaining <= 0) {
                clearInterval(timerInterval);
                actuallySubmit();
                return;
            }

            const m = Math.floor(timeRemaining / 60);
            const s = timeRemaining % 60;
            timerEl.textContent = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;

            if (timeRemaining <= 60) timerEl.classList.add('urgent');
            if (timeRemaining <= 10) play.tick();

        }, 1000);
    }

    // ── Anti-Cheat ──────────────────────────────────────────
    function setupAntiCheat() {
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) logViolation('Tab Switch');
        });
        document.addEventListener('fullscreenchange', () => {
            if (!document.fullscreenElement) logViolation('Fullscreen Exit');
        });
    }

    function logViolation(type) {
        play.warn();
        document.getElementById('anticheat-overlay').classList.add('visible');
        fetch('/contestant/anti-cheat-event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ event: type, test_id: testId })
        });
        // Auto-submit on 3rd violation or severe one? 
        // For now just warning as per requirements, but showing immersive overlay.
    }

    window.resumeTest = function() {
        enterFullscreen();
        document.getElementById('anticheat-overlay').classList.remove('visible');
    };

    // ── Submission ──────────────────────────────────────────
    window.confirmSubmit = function() {
        document.getElementById('submit-modal').classList.add('visible');
    };

    window.closeSubmitModal = function() {
        document.getElementById('submit-modal').classList.remove('visible');
    };

    window.actuallySubmit = function() {
        document.getElementById('submit-test-btn').disabled = true;
        document.getElementById('submit-test-btn').textContent = 'Submitting...';
        play.submit();
        
        fetch(`/contestant/submit-test`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ responses: responses })
        }).then(res => {
            if (res.ok) {
                window.location.href = `/contestant/thank-you?test_id=${testId}`;
            } else {
                toast('Error submitting test. Please try again.', 'err');
                document.getElementById('submit-test-btn').disabled = false;
                document.getElementById('submit-test-btn').textContent = 'Finalize Test &⚡';
            }
        });
    };

    // Initialize countdown on window load
    window.addEventListener('load', startCountdown);

})();
