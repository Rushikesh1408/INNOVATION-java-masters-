/* ProctorEx main.js — theme, toast, sounds, helpers */
(function () {
  'use strict';

  // ── Theme ──────────────────────────────────────────────────
  const root = document.documentElement;
  const saved = localStorage.getItem('px-theme') || 'dark';
  root.setAttribute('data-theme', saved);



  // ── Sound system ───────────────────────────────────────────
  let muted = localStorage.getItem('px-muted') === '1';

  function makeBeep(freq, dur, vol, type) {
    if (muted) return;
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain); gain.connect(ctx.destination);
      osc.type = type || 'sine';
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(vol || .3, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(.0001, ctx.currentTime + dur);
      osc.start(); osc.stop(ctx.currentTime + dur);
    } catch (e) { /* ignore */ }
  }

  window.sounds = {
    tick:   () => makeBeep(880, .08, .15, 'square'),
    select: () => makeBeep(660, .12, .2,  'sine'),
    warn:   () => makeBeep(440, .3,  .4,  'sawtooth'),
    submit: () => makeBeep(523, .5,  .35, 'sine'),
    final:  () => { makeBeep(880, .2, .5, 'square'); setTimeout(() => makeBeep(1100, .4, .5, 'sine'), 250); }
  };



  // ── Toast system ───────────────────────────────────────────
  const container = document.getElementById('toast-container');

  window.toast = function (msg, type, duration) {
    if (!container) return;
    const el = document.createElement('div');
    el.className = 'toast toast-' + (type || 'warn');
    el.textContent = msg;
    container.appendChild(el);
    setTimeout(() => {
      el.classList.add('toast-out');
      el.addEventListener('animationend', () => el.remove());
    }, duration || 3500);
  };

})();
