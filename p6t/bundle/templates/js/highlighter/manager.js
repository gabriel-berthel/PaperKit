import { glinerMatchesFetch } from '../api/gliner.js';
import { withUI } from '../dom/ui_freeze.js';
import { push } from '../dom/snapshots.js';

const ROOT_SELECTOR = '#app-content';
const CACHE_KEY = 'highlight_entities_v1';
const MARK_EXCLUDE = ['h1', 'h2', 'h3', 'pre', 'code'];
const COLORS = [
  '#fbbf24', '#34d399', '#60a5fa', '#f472b6',
  '#a78bfa', '#fb923c', '#22c55e', '#38bdf8',
  '#f43f5e', '#eab308', '#10b981', '#6366f1',
  '#ec4899', '#84cc16', '#0ea5e9', '#f97316',
];

export function toLabel(name) {
  return name.trim().toLowerCase().replace(/\s+/g, '_');
}

function save(entities) {
  localStorage.setItem(CACHE_KEY, JSON.stringify([...entities.entries()]));
}

function load() {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    return raw ? new Map(JSON.parse(raw)) : new Map();
  } catch { return new Map(); }
}

function mark(entities) {
  const root = document.querySelector(ROOT_SELECTOR);
  if (!root || !window.Mark) return;

  const marker = new window.Mark(root);
  const all = [...entities.entries()]
    .flatMap(([label, e]) => e.matches.flatMap(text => [
      { text, label, color: e.color },
      { text: `(${text})`, label, color: e.color },
    ]))
    .sort((a, b) => b.text.length - a.text.length);

  marker.unmark({ done: () => {
    for (const { text, label, color } of all) {
      if (!text?.trim()) continue;
      marker.mark(text, {
        separateWordSearch: false,
        accuracy: 'exactly',
        acrossElements: true,
        ignoreJoiners: true,
        element: 'mark',
        exclude: [...MARK_EXCLUDE, 'mark[data-type="entity"]'],
        each(el) {
          el.dataset.type = 'entity';
          el.dataset.label = label;
          el.style.setProperty('--entity-bg', color);
        },
      });
    }
  }});
}

class HighlightManager {
  #entities = load();

  list() {
    return [...this.#entities.entries()].map(([label, e]) => ({ label, ...e }));
  }

  _pickColor(entities) {
    const used = new Set([...entities.values()].map(e => e.color));
    return COLORS.find(c => !used.has(c)) ?? COLORS[0];
  }

  add(displayName) {
    const label = toLabel(displayName);
    if (this.#entities.has(label)) return;
    this.#entities.set(label, { displayName, matches: [], color: this._pickColor(this.#entities) });
    save(this.#entities);
  }

  remove(label) {
    this.#entities.delete(label);
    save(this.#entities);
    mark(this.#entities);
  }

  async run() {
    const entries = this.list();
    if (!entries.length) return 0;

    const allHaveMatches = entries.every(e => e.matches?.length);
    if (allHaveMatches) {
      this.restore();
      return entries.reduce((sum, e) => sum + e.matches.length, 0);
    }

    const results = await withUI(() => glinerMatchesFetch(entries.map(e => e.displayName)));
    let totalMatches = 0;
    for (const { label, displayName, color } of entries) {
      const matches = (results[displayName] ?? []).filter(Boolean);
      totalMatches += matches.length;
      this.#entities.set(label, { displayName, color, matches });
    }
    save(this.#entities);
    mark(this.#entities);
    push()
    return totalMatches;
  }

  restore() {
    mark(this.#entities);
  }

  _setEntities(map) {
    this.#entities = map;
    save(this.#entities);
  }
}

export const highlightManager = new HighlightManager();