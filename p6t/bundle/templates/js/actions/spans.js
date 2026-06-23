import { simplify, MODES, SREConvertion } from "../api/actions.js";
import { withUI } from "../dom/ui_freeze.js";
import { resolveRefs } from "../dom/prefetch.js";
import { jumpAndFlash } from "../dom/scroll.js";
import {
  footnoteToBullet,
  footnoteToTextRef,
  run_all_annotations,
  revertAnnotations,
} from "../marking/annotation.js";
import { push } from "../dom/snapshots.js";
import { removeEl } from "../dom/element.js";
import { openPopupMenu, initPopupMenu } from "../dom/popup_menu.js";

// ── Action functions ──────────────────────────────────────────────────────────

/** Unwraps a span element, leaving its children in place. */
function removeMarking(el) {
  const parent = el.parentNode;
  while (el.firstChild) {parent.insertBefore(el.firstChild, el);}
  parent.removeChild(el);
  parent.normalize();
  push();
}

function openUrlEl(el) {
  const url = el.dataset.url;
  if (!url) {return;}
  if (confirm(`Open link?\n${url}`)) {window.open(url, "_blank");}
}

/** Replaces an inline-maths span with plain speechified text then unwraps it. */
async function speechifyMathsEl(el) {
  const clone = revertAnnotations(el);
  await withUI(() => simplify(clone.dataset.latex, MODES.FORMULA))
    .then((result) => {
      el.textContent = result.text;
      el.replaceWith(...el.childNodes);
    })
    .catch(() => null);
  push();
}

/** Unwraps a span, keeping its text content. */
function toTextEl(el) {
  el.replaceWith(...el.childNodes);
  push();
}

async function summarizeInlineCaption(el) {
  await withUI(() => simplify(el.textContent, MODES.CAPTION))
    .then((result) => { el.innerHTML = `(${result.text})`; })
    .catch(() => null);
  push();
}

async function simplifyWordingEl(el) {
  const clone = revertAnnotations(el);
  await withUI(() => simplify(clone.textContent, MODES.WORDING))
    .then((result) => { el.innerHTML = `(${result.text})`; })
    .catch(() => null);
  push();
}

async function sreSpeechify(el) {
  const text = await SREConvertion(el.textContent);
  el.parentNode.insertBefore(document.createTextNode(text), el);
  el.remove();
  push();
}

// ── Match predicates ──────────────────────────────────────────────────────────

const isUrl            = (el) => !!el.dataset.url;
const isNotUrl         = (el) => !el.dataset.url;
const hasNoCaption     = (el) => el.nextElementSibling?.dataset.type !== "inline-caption";
const isFootnoteBullet = (el) => el.classList.contains("footnote-bullet");
const isTextRef        = (el) => el.classList.contains("text-ref");
const isNonNarrative   = (el) => el.dataset.narrative === "false";

// ── Action registry ───────────────────────────────────────────────────────────

const SPAN_ACTIONS = {
  "inline-maths": [
    { id: "speechify",  label: "LM Speechify", run: speechifyMathsEl },
    { id: "clearspeak", label: "Clearspeak",   run: sreSpeechify      },
    { id: "toText",     label: "To text",      run: toTextEl          },
  ],

  // table and figure share the same actions
  table:  captionActions(),
  figure: captionActions(),

  footnote: [
    { id: "open-url",             label: "Open link",            run: openUrlEl,        match: isUrl                                    },
    { id: "insert-caption-inline",label: "Insert caption in text",run: (el) => insertCaption(el, "inline"), match: (el) => isNotUrl(el) && hasNoCaption(el) },
    { id: "insert-caption-below", label: "Insert caption below", run: (el) => insertCaption(el, "below"),  match: isNotUrl                                 },
    { id: "to-text-ref",          label: "Turn to text ref",     run: footnoteToTextRef,match: isFootnoteBullet                          },
    { id: "to-bullet",            label: "Turn to bullet",       run: footnoteToBullet, match: isTextRef                                 },
    { id: "remove",               label: "Remove",               run: removeEl                                                          },
  ],

  "a-link": [
    { id: "open-url", label: "Open link", run: openUrlEl, match: isUrl },
    { id: "remove",   label: "Remove",    run: removeEl                },
  ],

  "inline-caption": [
    { id: "summarize", label: "Summarize",        run: summarizeInlineCaption },
    { id: "simplify",  label: "Simplify wording", run: simplifyWordingEl      },
    { id: "remove",    label: "Remove",           run: removeEl               },
  ],

  reference: [
    { id: "remove", label: "Remove", run: removeEl, match: isNonNarrative },
  ],

  entity: [
    { id: "remove-marking", label: "Remove", run: removeMarking },
  ],
};

function captionActions() {
  return [
    { id: "insert-caption-inline", label: "Insert caption in text", run: (el) => insertCaption(el, "inline"), match: hasNoCaption },
    { id: "insert-caption-below",  label: "Insert caption below",   run: (el) => insertCaption(el, "below")                      },
  ];
}

// ── Caption insertion ─────────────────────────────────────────────────────────

function buildCaptionText(el) {
  return resolveRefs(el)
    .filter((c) => c.caption)
    .map((c) => c.caption)
    .join(" ; ");
}

function insertCaptionInline(el, rawCaption) {
  const span         = document.createElement("span");
  span.dataset.type  = "inline-caption";
  span.innerHTML     = `(${rawCaption.replace(/[.;,]+$/, "")})`;

  el.insertAdjacentText("afterend", " ");
  el.insertAdjacentElement("afterend", span);

  // Strip "Table X" / "Figure X" labels from the inline caption.
  span.innerText  = span.innerText.replaceAll(/(Table|Figure)\s+\S+/gi, "");
  span.innerHTML  = run_all_annotations(span.innerText);

  jumpAndFlash(span, "#fde68a");
}

function insertCaptionBelow(el, rawCaption) {
  const block        = document.createElement("p");
  block.dataset.type = "paragraph";
  block.innerHTML    = run_all_annotations(rawCaption);

  // Insert after the last sibling bullet if we are inside a bullet list.
  const parent = el.closest('[data-type="paragraph"], [data-type="bullet"]') ?? el;
  let   anchor = parent;
  if (parent.dataset.type === "bullet") {
    while (anchor.nextElementSibling?.dataset.type === "bullet") {
      anchor = anchor.nextElementSibling;
    }
  }

  anchor.insertAdjacentElement("afterend", block);
  jumpAndFlash(block, "#fde68a");
}

function insertCaption(el, mode) {
  const caption = buildCaptionText(el);
  if (mode === "inline") {insertCaptionInline(el, caption);}
  if (mode === "below")  {insertCaptionBelow(el, caption);}
}

// ── Init ──────────────────────────────────────────────────────────────────────

export function initSpanActions() {
  initPopupMenu();

  document.getElementById("app-content").addEventListener("contextmenu", (e) => {
    const el      = e.target.closest("[data-type]");
    const actions = SPAN_ACTIONS[el?.dataset.type]?.filter(
      (a) => a.match?.(el) ?? true,
    );

    if (!el || !actions?.length) {return;}

    e.preventDefault();
    openPopupMenu(actions, el, e.clientX, e.clientY);
  });
}