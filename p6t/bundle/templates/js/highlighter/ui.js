import {highlightManager, toLabel} from './manager.js';

const MAX_ENTITIES = 16;
const chipList = document.getElementById('highlight-chips');
const addBtn   = document.getElementById('add-highlight');
const fab      = document.getElementById('highlight-fab');

function validate(value) {
  const trimmed = value?.trim().toLowerCase() ?? '';
  if (trimmed.length < 3)                return 'Name must be at least 3 characters';
  if (!/^[a-zA-Z0-9 ]+$/.test(trimmed)) return 'Only letters, numbers, and spaces allowed';
  if (highlightManager.list().length >= MAX_ENTITIES) return 'Max 16 entities reached';
  if (highlightManager.list().some(e => e.label === toLabel(trimmed))) return 'Already exists';
  return null;
}

function showError(msg) {
  let el = chipList.querySelector('.chip-error');
  if (!el) {
    el = Object.assign(document.createElement('div'), { className: 'chip-error' });
    chipList.appendChild(el);
  }
  el.textContent = msg;
  clearTimeout(el._t);
  el._t = setTimeout(() => el.remove(), 2000);
}

function buildChip({ label, displayName, color }) {
  const chip   = Object.assign(document.createElement('span'), { className: 'chip' });
  chip.dataset.label = label;
  const dot    = Object.assign(document.createElement('span'), { className: 'dot' });
  dot.style.background = color;
  const name   = Object.assign(document.createElement('span'), { className: 'chip-name', textContent: displayName });
  const remove = Object.assign(document.createElement('span'), { className: 'remove', textContent: '×' });
  remove.addEventListener('click', () => { highlightManager.remove(label); renderChips(); });
  chip.append(dot, name, remove);
  return chip;
}

function renderChips() {
  chipList.querySelectorAll('.chip').forEach(el => el.remove());
  for (const entity of highlightManager.list()) {
    chipList.insertBefore(buildChip(entity), addBtn);
  }
  addBtn.disabled = highlightManager.list().length >= MAX_ENTITIES;
}

async function startAddFlow() {
  const input = Object.assign(document.createElement('input'), {
    type: 'text', className: 'chip-input', placeholder: 'Term name…',
  });
  addBtn.replaceWith(input);
  input.focus();

  let done = false;

  function cancel() {
    if (done) return;
    done = true;
    input.replaceWith(addBtn);
  }

  function commit() {
    if (done) return;
    const error = validate(input.value);
    if (error) { showError(error); return; }
    done = true;
    highlightManager.add(input.value.trim().toLowerCase());
    input.replaceWith(addBtn);
    renderChips();
  }

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter')  commit();
    if (e.key === 'Escape') cancel();
  });
  input.addEventListener('blur', () => setTimeout(commit, 100));
}

fab.addEventListener('click', async () => {
  fab.disabled = true;
  try {
    const count = await highlightManager.run();
    if (count === 0) showError('No matches found in document');
  } catch {
    showError('Network error');
  } finally {
    fab.disabled = false;
  }
});

addBtn.addEventListener('click', startAddFlow);
renderChips();
highlightManager.restore();