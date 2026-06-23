import { simplify, MODES, SREConvertion, summarize} from "../api/actions.js";
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

/** Replaces an inline span with plain speechified text then unwraps it. */
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


async function sreSpeechify(el) {
  const text = await SREConvertion(el.textContent);

  el.parentNode.insertBefore(document.createTextNode(text), el);
  el.remove();
  push();
}

async function summarizeEl(el) {
  const clone = revertAnnotations(el);

  await withUI(
      () => {
        clone.querySelectorAll("[data-type='inline']").forEach(el => el.textContent = simplify(el.dataset.latex, MODES.FORMULA))
        let unannotated = revertAnnotations(clone).textContent;
        return summarize(unannotated);
      }
    )
    .then((result) => { el.innerHTML = run_all_annotations(result.text); })
    .catch(() => null);
  push();
}

async function simplifyWording(el) {
  const clone = revertAnnotations(el);

  await withUI(
      () => {
        clone.querySelectorAll("[data-type='inline']").forEach(el => el.textContent = simplify(el.dataset.latex, MODES.FORMULA))
        let unannotated = revertAnnotations(clone).textContent;
        return simplify(unannotated, MODES.WORDING);
      }
    )
    .then((result) => { el.innerHTML = run_all_annotations(result.text); })
    .catch(() => null);
  push();
}

async function toClearSpeakFormula(el) {
  el.innerHTML     = await SREConvertion(el.dataset.latex);
  el.dataset.type  = "paragraph";
  jumpAndFlash(el);
  push();
}

async function simplifyFormulaEl(el) {
  const text = await withUI(() => simplify(el.dataset.latex, MODES.FORMULA))
    .then((r) => r.text)
    .catch(() => null);

  el.textContent = text;
  el.dataset.type = "paragraph"
  jumpAndFlash(el);
  push();
}
async function describeCodeEl(el) {
  const text = await withUI(() => simplify(el.textContent, MODES.CODE))
    .then((r) => r.text)
    .catch(() => null);

  el.textContent = text;
  el.dataset.type = "paragraph"
  jumpAndFlash(el);
  push();
}


// ── Match predicates ──────────────────────────────────────────────────────────

const isUrl            = (el) => !!el.dataset.url;
const isNotUrl         = (el) => !el.dataset.url;
const hasNoCaption     = (el) => el.nextElementSibling?.dataset.type !== "caption";
const isFootnoteBullet = (el) => el.classList.contains("footnote-bullet");
const isTextRef        = (el) => el.classList.contains("text-ref");
const isNonNarrative   = (el) => el.dataset.narrative === "false";

// ── Action registry ───────────────────────────────────────────────────────────

const SPAN_ACTIONS = {
  inline: [
    { id: "speechify",  label: "LM Speechify", run: speechifyMathsEl },
    { id: "clearspeak", label: "Clearspeak",   run: sreSpeechify      },
  ],

  formula: [
    { id: "speechify",  label: "LM Speechify", run:  simplifyFormulaEl  },
    { id: "clearspeak", label: "Clearspeak",   run:  toClearSpeakFormula     },
  ],

  code: [
    { id: "describe",  label: "LM Describe", run: describeCodeEl },
  ],


  paragraph: [
    { id: "summarize",  label: "Summarize (ALL)", run: summarizeEl },
    { id: "summarize",  label: "Simplify wording (ALL)", run: simplifyWording },
  ],

  bullet: [
    { id: "summarize",  label: "Summarize ALL", run: summarizeEl },
    { id: "summarize",  label: "Simplify wording (ALL)", run: simplifyWording },
  ],

  // table and figure share the same actions
  table:  [{ id: "insert-caption-below",  label: "Insert caption below",   run: (el) => insertCaption(el, "below")}],
  figure: [{ id: "insert-caption-below",  label: "Insert caption below",   run: (el) => insertCaption(el, "below")}],

  footnote: [
    { id: "open-url",             label: "Open link",            run: openUrlEl,        match: isUrl                                    },
    { id: "insert-caption-below", label: "Insert caption below", run: (el) => insertCaption(el, "below"),  match: isNotUrl                                 },
    { id: "to-text-ref",          label: "Turn to text ref",     run: footnoteToTextRef,match: isFootnoteBullet                          },
    { id: "to-bullet",            label: "Turn to bullet",       run: footnoteToBullet, match: isTextRef                                 },
    { id: "remove",               label: "Remove",               run: removeEl                                                          },
  ],

  "a-link": [
    { id: "open-url", label: "Open link", run: openUrlEl, match: isUrl },
    { id: "remove",   label: "Remove",    run: removeEl                },
  ],

  reference: [
    { id: "remove", label: "Remove", run: removeEl, match: isNonNarrative },
  ],

  entity: [
    { id: "remove-marking", label: "Remove", run: removeMarking },
  ],
};


// ── Caption insertion ─────────────────────────────────────────────────────────

function buildCaptionText(el) {
  return resolveRefs(el)
    .filter((c) => c.caption)
    .map((c) => c.caption.trim())
    .join(" ; ");
}

function insertCaptionInline(el, rawCaption) {
  const span         = document.createElement("span");
  
  span.dataset.type  = "caption";

  rawCaption = ` (${rawCaption.replace(/[.;,]+$/, "")})`;
  rawCaption = rawCaption.replaceAll(/(Table|Figure)\s+\S+/gi, "");
  span.innerHTML = rawCaption

  // el.insertAdjacentText("afterend", " ");
  console.log(el)
  el.insertAdjacentElement("afterend", span);

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