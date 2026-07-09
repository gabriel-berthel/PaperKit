import {highlightManager} from "../highlighter/manager.js";

// ── Constants ─────────────────────────────────────────────────────────────────

const SNAPSHOT_KEY  = `app_snapshots_v1_${window.document_id}`;
const AUTOSAVE_ID   = "autosave";
const AUTOSAVE_NAME = "⏱ Last session (autosave)";
const BASE_NAME     = "Base Document";

// ── Module state ──────────────────────────────────────────────────────────────

const undoStack = [];
const redoStack = [];

let target             = null;
let undoBtn            = null;
let redoBtn            = null;
let snapshotBtn        = null;
let snapshotHistoryBtn = null;
let maxSize            = 100;

// ── State snapshot ────────────────────────────────────────────────────────────

function getState() {
  return {
    html:     target?.innerHTML ?? "",
    entities: [...highlightManager.list()],
  };
}

function applyState(state) {
  if (!target || !state) {return;}
  target.innerHTML = state.html;

  const map = new Map(
    state.entities.map(({ label, displayName, matches, color }) => [
      label,
      { displayName, matches, color },
    ]),
  );
  highlightManager._setEntities(map);
  highlightManager.restore();
}

// ── Undo / redo ───────────────────────────────────────────────────────────────

function updateButtons() {
  if (undoBtn) {undoBtn.disabled = undoStack.length <= 1;}
  if (redoBtn) {redoBtn.disabled = redoStack.length === 0;}
}

/** Snapshot the current state onto the undo stack and trigger an autosave. */
export function push() {
  if (!target) {return;}

  const state = getState(); // capture once, reuse for both undo stack and autosave
  undoStack.push(state);
  if (undoStack.length > maxSize) {undoStack.shift();}
  redoStack.length = 0;
  updateButtons();

  saveAutosave(state);
}

export function undo() {
  if (undoStack.length <= 1) return;

  const current = undoStack.pop();
  redoStack.push(current);

  const previous = undoStack[undoStack.length - 1];
  applyState(previous);

  updateButtons();
}

export function redo() {
  if (redoStack.length === 0) return;

  const next = redoStack.pop();
  undoStack.push(next);

  applyState(next);

  updateButtons();
}

export function clear() {
  redoStack.length = 0;

  undoStack.length = 0;
  undoStack.push(getState());

  updateButtons();
}

// ── Persistence helpers ───────────────────────────────────────────────────────

function loadSnapshots() {
  try {
    const raw = localStorage.getItem(SNAPSHOT_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveSnapshots(snapshots) {
  localStorage.setItem(SNAPSHOT_KEY, JSON.stringify(snapshots));
}

// ── Autosave ──────────────────────────────────────────────────────────────────

/**
 * Overwrites the single autosave entry. Accepts the already-captured state
 * so we don't call getState() a second time per push().
 */
function saveAutosave(state) {
  const snapshots = loadSnapshots().filter((s) => s.id !== AUTOSAVE_ID);
  snapshots.push({
    id:        AUTOSAVE_ID,
    name:      AUTOSAVE_NAME,
    timestamp: Date.now(),
    state,
  });
  saveSnapshots(snapshots);
}

// ── Named snapshots ───────────────────────────────────────────────────────────

export function listSnapshots() {
  return loadSnapshots().map(({ id, name, timestamp }) => ({ id, name, timestamp }));
}

export function saveSnapshot(name) {
  const snapshots = loadSnapshots();
  const finalName =
    name?.trim() ||
    `Snapshot ${snapshots.length + 1} — ${new Date().toLocaleString()}`;

  const snapshot = {
    id:        crypto.randomUUID(),
    name:      finalName,
    timestamp: Date.now(),
    state:     getState(),
  };
  snapshots.push(snapshot);
  saveSnapshots(snapshots);
  return snapshot;
}

export function loadSnapshot(id) {
  const snapshot = loadSnapshots().find((s) => s.id === id);
  if (!snapshot) {return false;}

  const confirmed = window.confirm(
    `Restore snapshot "${snapshot.name}"? This will replace the current content and clear the undo/redo history.`,
  );
  if (!confirmed) {return false;}

  applyState(snapshot.state);
  clear();
  return true;
}

export function deleteSnapshot(id) {
  saveSnapshots(loadSnapshots().filter((s) => s.id !== id));
}

// ── History menu ──────────────────────────────────────────────────────────────

/**
 * Clamps a { left, top } position so the element stays within the viewport.
 */
function clampToViewport(left, top, width, height) {
  const maxLeft = window.scrollX + document.documentElement.clientWidth  - width  - 8;
  const maxTop  = window.scrollY + document.documentElement.clientHeight - height - 8;
  return {
    left: Math.max(8, Math.min(left, maxLeft)),
    top:  Math.max(8, Math.min(top,  maxTop)),
  };
}

function positionHistoryMenu(menu) {
  const anchor   = snapshotHistoryBtn.getBoundingClientRect();
  const menuRect = menu.getBoundingClientRect();

  let top = anchor.bottom + window.scrollY;

  // Flip above the button if it doesn't fit below.
  if (top + menuRect.height > window.scrollY + document.documentElement.clientHeight - 8) {
    top = anchor.top + window.scrollY - menuRect.height;
  }

  const clamped = clampToViewport(
    anchor.left + window.scrollX,
    top,
    menuRect.width,
    menuRect.height,
  );

  menu.style.left = `${clamped.left}px`;
  menu.style.top  = `${clamped.top}px`;
}

function buildSnapshotRow(id, name, timestamp, onDeleted) {
  const row         = document.createElement("div");
  row.className     = "snapshot-row";

  const label       = document.createElement("span");
  label.className   = "snapshot-label";
  label.textContent = name;
  label.title       = new Date(timestamp).toLocaleString();
  label.onclick     = () => loadSnapshot(id);
  row.appendChild(label);

  // Base Document is protected from deletion.
  if (name !== BASE_NAME) {
    const del         = document.createElement("button");
    del.className     = "snapshot-delete";
    del.textContent   = "✕";
    del.title         = "Delete snapshot";
    del.onclick       = (e) => {
      e.stopPropagation();
      if (!window.confirm(`Delete snapshot "${name}"?`)) {return;}
      deleteSnapshot(id);
      onDeleted();
    };
    row.appendChild(del);
  }

  return row;
}

function openHistoryMenu() {
  // Toggle: if already open, close it.
  const existing = document.getElementById("snapshot-history-menu");
  if (existing) { existing.remove(); return; }

  const menu    = document.createElement("div");
  menu.id       = "snapshot-history-menu";

  const refresh = () => { menu.remove(); openHistoryMenu(); };

  const snapshots = listSnapshots().slice().reverse();

  if (!snapshots.length) {
    const empty       = document.createElement("div");
    empty.className   = "snapshot-empty";
    empty.textContent = "No snapshots yet";
    menu.appendChild(empty);
  } else {
    for (const { id, name, timestamp } of snapshots) {
      menu.appendChild(buildSnapshotRow(id, name, timestamp, refresh));
    }
  }

  document.body.appendChild(menu);
  positionHistoryMenu(menu);

  // Dismiss on click outside. Using pointerdown + requestAnimationFrame avoids
  // the setTimeout(0) hack while still missing the triggering click.
  requestAnimationFrame(() => {
    document.addEventListener("pointerdown", function dismiss(e) {
      if (!menu.contains(e.target) && e.target !== snapshotHistoryBtn) {
        menu.remove();
        document.removeEventListener("pointerdown", dismiss);
      }
    });
  });
}

// ── Init ──────────────────────────────────────────────────────────────────────

export function initSnapshots(options = {}) {
  target             = document.querySelector(options.target             ?? "#app-content");
  undoBtn            = document.querySelector(options.undoBtn            ?? "#undo-btn");
  redoBtn            = document.querySelector(options.redoBtn            ?? "#redo-btn");
  snapshotBtn        = document.querySelector(options.snapshotBtn        ?? "#snapshot-btn");
  snapshotHistoryBtn = document.querySelector(options.snapshotHistoryBtn ?? "#snapshot-history-btn");

  if (options.maxSize) {maxSize = options.maxSize;}

  undoBtn?.addEventListener("click", undo);
  redoBtn?.addEventListener("click", redo);

  snapshotBtn?.addEventListener("click", () => {
    const name = window.prompt("Snapshot name (optional):", "");
    if (name === null) {return;} // user cancelled the prompt
    saveSnapshot(name);
  });

  snapshotHistoryBtn?.addEventListener("click", openHistoryMenu);

  if (target) {
    if (listSnapshots().length === 0) {
      saveSnapshot(BASE_NAME);
    } else {
      maybeOfferAutosave();
    }
  }

  clear()
}

// ── Autosave recovery ─────────────────────────────────────────────────────────

function maybeOfferAutosave() {
  const autosave = loadSnapshots().find((s) => s.id === AUTOSAVE_ID);
  if (!autosave) {return;}

  const restore = window.confirm(
    `An autosave from ${new Date(autosave.timestamp).toLocaleString()} was found. Restore it?`,
  );

  // On decline: do nothing. The document and highlight state are already correct
  // from the initial load; resetting entities here would wipe valid state.
  if (!restore) {return;}

  applyState(autosave.state);
  clear();
}