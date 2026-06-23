import { expandAbbreviations } from "./abbreviations.js"
import { SREConvertion } from "../api/actions.js";

export function speechify(el) {
  const type = el.dataset.type;

  if (['paragraph', 'bullets', 'caption-bloc'].includes(type)) {
    return paragraphToSpeech(el);
  }

  return el.textContent.trim();
}

function normalizeSlashes(text) {
  return text.replace(/\b(\w+)\/(\w+)\b/g, (m, a, b) => {
    return `${a} slash ${b}`;
  });
}

export function paragraphToSpeech(el) {
  const clone = el.cloneNode(true);

  // STEP 1: remove non-narrative references
  clone
    .querySelectorAll('[data-type="reference"][data-narrative="false"]')
    .forEach(node => node.remove());

  clone
    .querySelectorAll('[data-type="footnote"]')
    .forEach(node => node.remove());

  // STEP 2: bracket references
  clone
    .querySelectorAll('[data-type="reference"][data-kind="bracket"]')
    .forEach(node => {
      const tooltip = node.getAttribute('data-tooltip') || '';
      node.textContent = tooltip ? `reference ${tooltip}` : 'reference';
    });


  let text = clone.textContent;

  text = expandAbbreviations(text)

  text = normalizeSlashes(text)

  // STEP 7: final cleanup
  return text.replace(/\s+/g, ' ').trim();
}
