import {fetchWhatIsIt, MODES, simplify, summarize} from "../api/actions.js";
import {withUI} from "../dom/ui_freeze.js";
import {state} from "../state.js";
import {revertAnnotations, run_all_annotations} from "../marking/annotation.js";
import {push} from "../dom/snapshots.js";
import {resolveElement, typeSelector} from "../dom/element.js";

// ── Constants ─────────────────────────────────────────────────────────────────

const MIN_WORDS_FOR_SIMPLIFY = 6;

/**
 * Element types that snap the selection to their outer boundary when partially
 * selected (tables, figures, etc. should always be selected whole or not at all).
 */
const SNAP_SELECTOR = typeSelector("table", "figure", "reference", "footnote", "inline");

/**
 * Element types that can host a selection toolbar (paragraph-level blocks).
 */
const TOOLBAR_SELECTOR = typeSelector("paragraph", "bullet");

// ── Toolbar state ─────────────────────────────────────────────────────────────

let toolbar = null;
const content = document.getElementById("app-content");

// ── Predicates ────────────────────────────────────────────────────────────────
//
// Pure functions (text: string, multiBlock: boolean) => boolean.
// Keeping them separate makes them independently testable.

const wordCount         = (str) => str.trim().split(/\s+/).filter(Boolean).length;
const isShortSelection  = (text) => wordCount(text) <= 6;
const isLongEnough      = (text) => wordCount(text) >= MIN_WORDS_FOR_SIMPLIFY;

const canGroup      = (_text, multiBlock) => multiBlock;
const canSimplify   = (text,  multiBlock) => !multiBlock && isLongEnough(text);
const canExplain    = (text,  multiBlock) => !multiBlock && isShortSelection(text);
const canRemove     = () => true;
const canCancel     = () => true;

const ACTION_CONDITIONS = {
  group:             canGroup,
  "simplify-student": canSimplify,
  "simplify-expert":  canSimplify,
  "summarize":  canSimplify,
  explain:           canExplain,
  remove:            canRemove,
  cancel:            canCancel,
};

// ── API actions ───────────────────────────────────────────────────────────────

/**
 * Returns a detached <div> containing a clone of the current selection's
 * contents, or null when nothing is selected.
 */
function cloneSelectionToDiv() {
  const sel = window.getSelection();
  if (!sel?.rangeCount) {return null;}

  const container = document.createElement("div");
  for (let i = 0; i < sel.rangeCount; i++) {
    container.appendChild(sel.getRangeAt(i).cloneContents());
  }
  return container;
}

async function runSimplify(mode) {
  const clone = cloneSelectionToDiv();
  if (!clone) {return;}
  await withUI(
      () => {
        clone.querySelectorAll("[data-type='inline']").forEach(el => el.textContent = simplify(el.dataset.latex, MODES.FORMULA))
        let unannotated = revertAnnotations(clone).textContent;
        
        return simplify(unannotated, mode);
      }
    )
    .then((result) => replaceSelection(result.text))
    .catch(() => null);
  push();
}

async function runSummary() {
  const clone = cloneSelectionToDiv();
  if (!clone) {return;}

  await withUI(
    () => {
      clone.querySelectorAll("[data-type='inline']").forEach(el => el.textContent = simplify(el.dataset.latex, MODES.FORMULA))
      let unannotated = revertAnnotations(clone).textContent;
      
      return summarize(unannotated);
    }
  )
    .then((result) => replaceSelection(result.text))
    .catch(() => null);
  push();
}

async function runSimplifyStudent() { await runSimplify(MODES.STUDENT); }
async function runSimplifyExpert()  { await runSimplify(MODES.EXPERT);  }

async function runExplain() {
  const term    = window.getSelection().toString().trim();
  const context = getSelectionContext();
  await withUI(() => fetchWhatIsIt(term, context))
    .then((result) => showExplainModal(term, result.text))
    .catch(() => null);
}

// ── Local actions ─────────────────────────────────────────────────────────────

function runGroup() {
  const sel = window.getSelection();
  if (!sel?.rangeCount) {return;}

  const range    = sel.getRangeAt(0);
  const ancestor =
    range.commonAncestorContainer.nodeType === Node.TEXT_NODE
      ? range.commonAncestorContainer.parentElement
      : range.commonAncestorContainer;

  const blocks = [...ancestor.querySelectorAll(TOOLBAR_SELECTOR)].filter((b) =>
    range.intersectsNode(b),
  );
  if (blocks.length < 2) {return;}

  const [first, ...rest] = blocks;
  rest.forEach((block) => {
    first.innerHTML += " " + block.innerHTML;
    block.remove();
  });
  sel.removeAllRanges();
  push();
}

function runRemove() {
  const sel = window.getSelection();
  if (!sel?.rangeCount) {return;}
  sel.getRangeAt(0).deleteContents();
  sel.removeAllRanges();
  push();
}

function runCancel() {
  window.getSelection()?.removeAllRanges();
}

// ── Action registry ───────────────────────────────────────────────────────────

const ACTIONS = [
  { id: "group",            label: "🔗 Group",             run: runGroup            },
  { id: "remove",           label: "🗑️ Remove",            run: runRemove           },
  { id: "summarize",  label: "💬 Summarize",  run: runSummary   },
  { id: "simplify-student", label: "🎓 Simplify (Student)", run: runSimplifyStudent  },
  { id: "simplify-expert",  label: "🧠 Simplify (Expert)",  run: runSimplifyExpert   },
  { id: "explain",          label: "📖 Explain",            run: runExplain          },
  { id: "cancel",           label: "✕",                    run: runCancel           },
];

// ── Toolbar DOM ───────────────────────────────────────────────────────────────

function createToolbar() {
  const el    = document.createElement("div");
  el.id       = "selection-toolbar";

  for (const action of ACTIONS) {
    const btn           = document.createElement("button");
    btn.dataset.action  = action.id;
    btn.textContent     = action.label;
    btn.onclick         = async () => {
      await action.run();
      el.classList.remove("visible");
    };
    el.appendChild(btn);
  }

  document.body.appendChild(el);
  return el;
}

function updateToolbarButtons(text, multiBlock) {
  for (const action of ACTIONS) {
    const btn = toolbar.querySelector(`[data-action="${action.id}"]`);
    if (!btn) {continue;}
    btn.hidden = !(ACTION_CONDITIONS[action.id]?.(text, multiBlock) ?? true);
  }
}

function positionToolbar(sel) {
  if (!sel?.rangeCount) {return;}

  const rects  = sel.getRangeAt(0).getClientRects();
  if (!rects.length) {return;}

  const first  = rects[0];
  const last   = rects[rects.length - 1];
  const tbW    = toolbar.offsetWidth  || 180;
  const tbH    = toolbar.offsetHeight || 40;

  let left = first.left + window.scrollX + (last.right - first.left) / 2 - tbW / 2;
  let top  = last.bottom + window.scrollY + 16;

  left = Math.max(window.scrollX + 8, Math.min(left, window.scrollX + window.innerWidth - tbW - 8));

  if (top + tbH > window.scrollY + window.innerHeight - 8) {
    top = first.top + window.scrollY - tbH - 16;
  }

  toolbar.style.left = `${left}px`;
  toolbar.style.top  = `${top}px`;
}

// ── Init ──────────────────────────────────────────────────────────────────────

export function initSelectionToolbar() {
  toolbar = createToolbar();

  let debounceTimer = null;

  function hideToolbar() {
    clearTimeout(debounceTimer);
    toolbar.classList.remove("visible");
    window.getSelection()?.removeAllRanges();
  }

  content.addEventListener("mouseup", () => {
    if (state.editor) {return;}
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      const sel = window.getSelection();
      if (!sel || sel.isCollapsed) { hideToolbar(); return; }

      if (!resolveElement(sel.anchorNode)?.closest(TOOLBAR_SELECTOR)) {
        hideToolbar();
        return;
      }

      const result = snapToDataTypeBoundaries(sel);
      if (!result?.text) { hideToolbar(); return; }

      updateToolbarButtons(result.text, result.multiBlock);
      toolbar.classList.add("visible");
      positionToolbar(sel);
    }, 150);
  });

  content.addEventListener("mousedown", (e) => {
    if (!toolbar.contains(e.target)) {hideToolbar();}
  });

  content.addEventListener("keydown", (e) => {
    if (state.editor) {return;}
    if (e.key === "Escape") {
      window.getSelection()?.removeAllRanges();
      hideToolbar();
      return;
    }
    if (!toolbar.contains(document.activeElement)) {hideToolbar();}
  });

  content.addEventListener("selectionchange", () => {
    if (state.editor) {return;}
    if (window.getSelection()?.isCollapsed) {toolbar.classList.remove("visible");}
  });

  content.addEventListener("scroll", hideToolbar, true);

  document.getElementById("edit-btn").addEventListener("click", hideToolbar);
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function getSelectionContext() {
  const sel = window.getSelection();
  if (!sel?.rangeCount) {return "";}
  const node      = sel.getRangeAt(0).startContainer;
  const paragraph = resolveElement(node).closest("p");
  return paragraph?.textContent.trim() ?? "";
}

function showExplainModal(term, result) {
  document.getElementById("define-modal")?.remove();

  const dialog  = document.createElement("dialog");
  dialog.id     = "define-modal";
  dialog.innerHTML = `
    <div class="define-term">${term}</div>
    <div class="define-body">${result?.trim() || "No definition found."}</div>
    <form method="dialog"><button>Dismiss</button></form>
  `;
  dialog.addEventListener("click", (e) => { if (e.target === dialog) {dialog.close();} });
  document.body.appendChild(dialog);
  dialog.showModal();
}

function snapToWordBoundaries(range) {
  if (range.startContainer.nodeType === Node.TEXT_NODE) {
    const node  = range.startContainer;
    let   start = range.startOffset;
    while (start > 0 && /\S/.test(node.textContent[start - 1])) {start--;}
    range.setStart(node, start);
  }

  if (range.endContainer.nodeType === Node.TEXT_NODE) {
    const node = range.endContainer;
    let   end  = range.endOffset;
    while (end < node.textContent.length && /\S/.test(node.textContent[end])) {end++;}
    range.setEnd(node, end);
  }
}

function isSameBlock(range) {
  const startBlock = resolveElement(range.startContainer).closest(TOOLBAR_SELECTOR);
  const endBlock   = resolveElement(range.endContainer).closest(TOOLBAR_SELECTOR);
  return startBlock && startBlock === endBlock;
}

/**
 * Expands the selection so it never partially overlaps snap-boundary elements.
 * Returns { text, multiBlock } or null if the selection is entirely inside a
 * snap element (e.g. both endpoints inside the same table).
 */
function snapToDataTypeBoundaries(sel) {
  if (!sel.rangeCount) {return null;}

  const range     = sel.getRangeAt(0);
  const startHost = resolveElement(range.startContainer).closest(SNAP_SELECTOR);
  const endHost   = resolveElement(range.endContainer).closest(SNAP_SELECTOR);

  // Selection confined to a single snap element → ignore it.
  if (startHost && startHost === endHost) {return null;}

  if (startHost) {range.setStartBefore(startHost);}
  if (endHost)   {range.setEndAfter(endHost);}

  if (startHost || endHost) {
    sel.removeAllRanges();
    sel.addRange(range);
  }

  snapToWordBoundaries(range);

  return {
    text:       sel.toString().trim(),
    multiBlock: !isSameBlock(range),
  };
}

function replaceSelection(html) {
  const sel = window.getSelection();
  if (!sel?.rangeCount) {return;}

  const range = sel.getRangeAt(0);
  range.deleteContents();

  const frag = range.createContextualFragment(run_all_annotations(html));
  range.insertNode(frag);
  range.collapse(false);
  sel.removeAllRanges();
  sel.addRange(range);
}