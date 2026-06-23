import { simplify, MODES, summarize, SREConvertion } from "../api/actions.js";
import { withUI } from "../dom/ui_freeze.js";
import { revertAnnotations, run_all_annotations } from "../marking/annotation.js";
import { playFrom } from "../tts/player.js";
import { push } from "../dom/snapshots.js";
import { jumpAndFlash } from "../dom/scroll.js";
import { removeEl, makeDataTypeEl } from "../dom/element.js";

// ── Action functions ──────────────────────────────────────────────────────────

/**
 * Splits the child nodes of `el` into sentence-boundary groups.
 * Text nodes are split on sentence-ending punctuation; element nodes are kept
 * whole and appended to the current group.
 */
function splitSentences(el) {
  const sentences = [];
  let   current   = [];

  for (const node of el.childNodes) {
    if (node.nodeType === Node.TEXT_NODE) {
      const parts = node.textContent.split(/(?<=[.!?])\s+/);
      parts.forEach((part, i) => {
        if (i > 0 && current.length > 0) {
          sentences.push(current);
          current = [];
        }
        if (part) {current.push(document.createTextNode(part));}
      });
    } else {
      current.push(node);
    }
  }

  if (current.length > 0) {sentences.push(current);}
  return sentences;
}

function bulletizeEl(el) {
  const sentences = splitSentences(el);
  if (!sentences.length) {return;}

  for (const nodes of sentences) {
    const bullet = makeDataTypeEl("bullet");
    nodes.forEach((node) => bullet.appendChild(node.cloneNode(true)));
    el.insertAdjacentElement("beforebegin", bullet);
  }

  el.remove();
  push();
}

function toParagraphEl(el) {
  const paragraph = makeDataTypeEl("paragraph");
  el.childNodes.forEach((node) => paragraph.appendChild(node.cloneNode(true)));
  el.replaceWith(paragraph);
  push();
}

/**
 * Replaces a formula block with a plain paragraph containing the speechified text.
 * Flashes the new paragraph (not the removed element).
 */
async function simplifyFormulaEl(el) {
  const text = await withUI(() => simplify(el.dataset.latex, MODES.FORMULA))
    .then((r) => r.text)
    .catch(() => null);

  const paragraph = makeDataTypeEl("paragraph");
  paragraph.textContent = text;
  el.insertAdjacentElement("beforebegin", paragraph);
  el.remove();
  jumpAndFlash(paragraph);
  push();
}


// ── Action registry ───────────────────────────────────────────────────────────
//
// Each entry: { id, tooltip, icon, run, match? }
// `match` is an optional predicate (el) => boolean; omit to always show.

const PLAY       = { id: "playTTS",      tooltip: "Play",         icon: "▶️", run: playFrom      };
const DELETE     = { id: "removeEl",     tooltip: "Delete",       icon: "❌", run: removeEl      };
const BULLETIZE  = { id: "bulletize",    tooltip: "Bulletize",    icon: "●", run: bulletizeEl   };
const PARAGRAPHI = { id: "paragraphize", tooltip: "Make paragraph",icon: "§",run: toParagraphEl };

const BLOCK_ACTIONS = {
  paragraph:      [PLAY, BULLETIZE, DELETE],
  bullet:         [PLAY, PARAGRAPHI, DELETE],
  heading:        [PLAY, PARAGRAPHI, DELETE],
  code: [
    PLAY,
    DELETE,
  ],
  formula: [
    PLAY,
    DELETE,
  ],
};

// ── Block toolbar ─────────────────────────────────────────────────────────────

let currentActions = null;

/**
 * Positions the block toolbar to the left of the element, vertically centred.
 * Accounts for toolbar width so it never clips at the left viewport edge.
 */

function positionActions(wrap, el) {
  const rect = el.getBoundingClientRect()
  wrap.style.left = `${rect.left - 40}px`
  wrap.style.top  = `${rect.top + rect.height / 2}px`
}

function buildBlockActions(targetEl, actions) {
  const wrap       = document.createElement("div");
  wrap.className   = "block-actions";

  for (const action of actions) {
    const btn             = document.createElement("button");
    btn.dataset.action    = action.id;
    btn.dataset.tooltip   = action.tooltip;
    btn.textContent       = action.icon;
    btn.onclick           = async () => {
      await action.run(targetEl);
      removeCurrentActions();
    };
    wrap.appendChild(btn);
  }

  return wrap;
}

function removeCurrentActions() {
  currentActions?.remove();
  currentActions = null;
}

// ── Init ──────────────────────────────────────────────────────────────────────

export function initBlockActions() {
  const content = document.getElementById("app-content");

  // Show toolbar on hover.
  content.addEventListener("mouseenter", (e) => {
    const el      = e.target.closest("[data-type]");
    const actions = BLOCK_ACTIONS[el?.dataset.type]?.filter(
      (a) => a.match?.(el) ?? true,
    );
    if (!el || !actions?.length) {return;}

    removeCurrentActions();
    currentActions = buildBlockActions(el, actions);
    document.body.appendChild(currentActions);
    positionActions(currentActions, el);
  }, true);

  // Hide while a selection is being dragged; restore if selection collapses.
  document.addEventListener("mousedown", (e) => {
    if (currentActions?.contains(e.target)) {return;}
    currentActions?.style.setProperty("visibility", "hidden");
  });

  document.addEventListener("mouseup", () => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) {
      currentActions?.style.removeProperty("visibility");
    }
  });

  // Destroy on scroll — position is stale.
  document.addEventListener("scroll", removeCurrentActions, true);
}