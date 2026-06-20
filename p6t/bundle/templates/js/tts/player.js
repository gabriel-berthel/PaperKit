// tts-player.js
import { jumpAndFlash } from '../dom/scroll.js';
import { fetchAudio } from '../api/tts.js';
import { speechify } from './speech.js';
import { exportAudio } from './export.js';

let elements = [];
let currentIndex = -1;
let autoAdvance = false;
let isPlaying = false;
let mutationObserver = null;

let playBtn, pauseBtn, nextBtn, prevBtn, autoToggle, labelEl;

const FLASH_COLOR = '#a7d8ff';

function firstWords(text, n = 6) {
  const words = text.split(/\s+/);
  const slice = words.slice(0, n).join(' ');
  return slice + (words.length > n ? '…' : '');
}

function updateLabel(text = null) {
  if (!labelEl) return;
  if (text !== null) {
    labelEl.textContent = text;
    return;
  }
  if (currentIndex < 0 || !elements[currentIndex]) {
    labelEl.textContent = '—';
    return;
  }
  labelEl.textContent = firstWords(speechify(elements[currentIndex]));
}

function highlightCurrent() {
  elements.forEach((el, i) => {
    el.classList.toggle('tts-active', i === currentIndex);
  });
}

// ---- Speak backend (Piper via tts-endpoint.js) ----
let activeToken = 0;
let currentAudio = null;

function speak(text, { onEnd, onError }) {
  const token = ++activeToken;

  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }

  fetchAudio(text)
    .then(url => {
      if (token !== activeToken) return; // superseded

      const audio = new Audio(url);
      currentAudio = audio;

      audio.onended = () => { if (token === activeToken) onEnd(); };
      audio.onerror = (e) => { if (token === activeToken) onError?.(e); };

      audio.play().catch(err => {
        if (token === activeToken) onError?.(err);
      });
    })
    .catch(err => {
      if (token === activeToken) onError?.(err);
    });
}

function cancelSpeak() {
  activeToken++;
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
}
// ----------------------------------------------------------

function speakIndex(index) {
  if (index < 0 || index >= elements.length) {
    stop();
    return;
  }

    // prefetching ahead.
  [index + 1, index + 2, index + 3]
    .filter(i => i >= 0 && i < elements.length)
    .forEach(i => fetchAudio(speechify(elements[i])));

  currentIndex = index;
  updateLabel();
  highlightCurrent();
  jumpAndFlash(elements[index], FLASH_COLOR);

  const text = speechify(elements[index]);

  if (!text) {
    if (autoAdvance) {
      speakIndex(index + 1);
    } else {
      isPlaying = false;
      updateButtons();
    }
    return;
  }

  isPlaying = true;
  updateButtons();

  speak(text, {
    onEnd: () => {
      if (autoAdvance) {
        speakIndex(currentIndex + 1);
      } else {
        isPlaying = false;
        updateButtons();
      }
    },
    onError: (e) => {
      console.error('TTS error:', e);
      isPlaying = false;
      updateLabel('Playback error');
      updateButtons();
    },
  });


}

function play() {
  if (currentIndex < 0) {
    speakIndex(0);
  } else if (!isPlaying) {
    speakIndex(currentIndex);
  }
}

function pause() {
  stop();
}

function next() {
  speakIndex(currentIndex + 1);
}

function prev() {
  speakIndex(currentIndex - 1);
}

function stop() {
  cancelSpeak();
  isPlaying = false;
  highlightCurrent();
  updateButtons();
  updateLabel();
}

function updateButtons() {
  if (playBtn) playBtn.style.display = isPlaying ? 'none' : 'inline-block';
  if (pauseBtn) pauseBtn.style.display = isPlaying ? 'inline-block' : 'none';
  if (prevBtn) prevBtn.disabled = currentIndex <= 0;
  if (nextBtn) nextBtn.disabled = currentIndex < 0 || currentIndex >= elements.length - 1;
}

// ---- Public API ----

export function playFrom(element) {
  const index = elements.indexOf(element);
  if (index === -1) return;
  speakIndex(index);
}

export function refreshElements(selector = '#app-content > *') {
  elements = [...document.querySelectorAll(selector)];

  if (currentIndex >= elements.length) {
    stop();
    currentIndex = -1;
  } else {
    updateButtons();
    updateLabel();
  }
}

function setupMutationObserver() {
  const root = document.querySelector('#app-content');
  if (!root) return;

  mutationObserver = new MutationObserver(() => {
    if (isPlaying) pause();
  });

  mutationObserver.observe(root, {
    childList: true,
    subtree: true,
    characterData: true,
  });
}

export function initTTS(options = {}) {
  playBtn    = document.querySelector(options.playBtn    || '#tts-play-btn');
  pauseBtn   = document.querySelector(options.pauseBtn   || '#tts-pause-btn');
  nextBtn    = document.querySelector(options.nextBtn    || '#tts-next-btn');
  prevBtn    = document.querySelector(options.prevBtn    || '#tts-prev-btn');
  autoToggle = document.querySelector(options.autoToggle || '#tts-auto-toggle');
  labelEl    = document.querySelector(options.labelEl    || '#tts-label');

  refreshElements(options.selector);
  setupMutationObserver();

  if (playBtn) playBtn.addEventListener('click', play);
  if (pauseBtn) pauseBtn.addEventListener('click', pause);
  if (nextBtn) nextBtn.addEventListener('click', next);
  if (prevBtn) prevBtn.addEventListener('click', prev);
  if (autoToggle) {
    autoToggle.checked = autoAdvance;
    autoToggle.addEventListener('change', (e) => {
      autoAdvance = e.target.checked;
    });
  }

  updateButtons();
  updateLabel();

  // export func;
  const exportBtn = document.querySelector(options.exportBtn || '#export-tts-btn');
  if (exportBtn) exportBtn.addEventListener('click', exportAudio);
}