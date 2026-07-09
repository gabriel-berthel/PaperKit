import {AUTHOR_YEAR_RE, IN_TEXT_AUTHOR_YEAR, REF_BRACKET_RE, REF_RE, STOP_WORD_REF} from './regex.js';
import {extractUrl, maskTags} from '../dom/utils.js';

// ── Annotators ────────────────────────────────────────────────────────────────

export function markInlineMaths(text) {
  return text.replace(
    /\$(.*?)\$/g,
    (_, content) =>
      ` <span data-type="inline" data-latex="${content}">$ ${content} $</span>`
  );
}

export function markTextRefs(text) {
  const masked = maskTags(text);
  let result = text;

  for (const match of masked.matchAll(new RegExp(REF_RE.source, 'gi'))) {
    const fullMatch = match[0];
    const kind = match[1];
    const refsRaw = match[2];

    const allRefs = [];
    for (const part of refsRaw.split(/\s*(?:and|or|,)\s*/)) {
      if (part.includes('-')) {
        const [a, b] = part.split('-').map(Number);
        for (let i = a; i <= b; i++) allRefs.push(String(i));
      } else {
        allRefs.push(part.trim());
      }
    }

    const refList = `[${allRefs.join(',')}]`;
    const replacement = `<span class='text-ref' data-type='${kind.toLowerCase()}' data-refs='${refList}'>${fullMatch}</span>`;
    result = result.replace(fullMatch, replacement);
  }

  return result;
}

export function markFootnotes(text) {
  return text.replace(
    /<sup>(.*?)<\/sup>/g,
    (_, content) =>
      ` <span class="text-ref" data-type="footnote" data-refs="[${content}]">footnote ${content}</span>`
  );
}


export function linkify(text) {
  return text.replace(/https?:\/\/[^\s]+/gi, (raw) => {
    // split URL from trailing punctuation
    const match = raw.match(/^(.*?)([)\].,!?;:…]*)$/);

    const url = match ? match[1] : raw;
    const trailing = match ? match[2] : "";

    const label = new URL(url)
      .hostname
      .replace(/^www\./, "")
      .split(".")[0];

    return `<a data-url="${url}" data-type="a-link" >${label}</a>${trailing}`;
  });
}

export function markReferences(text) {
  let masked = maskTags(text);

  // Collect stop-word-preceded references
  const narrativeRefs = new Set();
  for (const match of masked.matchAll(new RegExp(STOP_WORD_REF.source, 'gi'))) {
    narrativeRefs.add(match[1]);
  }

  masked = maskTags(text);

  // author year
  for (const reference of masked.matchAll(AUTHOR_YEAR_RE)) {
    const isNarrative = narrativeRefs.has(reference);
    
    text = text.replace(reference, `<span class="reference"
          data-type="reference"
          data-kind="author_year"
          data-narrative="${isNarrative}"
          data-tooltip="${reference}">` +
        `${isNarrative ? reference : '[ref]'}` +
        `</span>`)
    }

    masked = maskTags(text);

    for (const reference of masked.matchAll(REF_BRACKET_RE)) {
      const isNarrative = narrativeRefs.has(reference);

      text =text.replace(reference, `<span class="reference"
      data-type="reference"
      data-kind="bracket"
      data-narrative="${isNarrative}"
      data-tooltip="${reference}">
      ${isNarrative ? reference : '[ref]'}
      </span>`)
    }

    masked = maskTags(text);

     // Inline narrative: Smith et al. (2022)
    for (const reference of masked.matchAll(IN_TEXT_AUTHOR_YEAR)) {
  
      text =text.replace(reference, `<span class="reference"
      data-type="reference"
      data-kind="author_year"
      data-narrative="true">
      ${reference}
    </span>`)
    }
    
    return text;
}

export function revertAnnotations(root) {
  const clone = root.cloneNode(true);

  clone.querySelectorAll('[data-narrative="false"]').forEach(el => {
    const tooltip = el.getAttribute('title') ?? el.getAttribute('data-tooltip') ?? '';
    el.replaceWith(document.createTextNode(tooltip));
    console.log(tooltip)
  });

  clone.querySelectorAll('.footnote-bullet').forEach(el => {
    el.replaceWith(document.createTextNode(`footnote ${el.textContent}`));
  });

  return clone;
}

/**
 * Run all annotators in order.
 */
export function run_all_annotations(text) {

  text = markInlineMaths(text);
  text = markReferences(text);
  text = markTextRefs(text);
  text = markFootnotes(text);
  text = linkify(text)
  
  return text;
}

export function convert_all_footnotes_to_bullet() {
  document.querySelectorAll('.text-ref[data-type="footnote"]').forEach(footnoteToBullet)
}

export function footnoteToTextRef(el) {
  const span = document.createElement('span')
  span.className = 'text-ref'
  span.dataset.type = 'footnote'
  span.dataset.refs = el.dataset.refs ?? ''
  let ref = span.dataset.refs.slice(1, -1);
  span.textContent = `footnote ${ref}`

  el.insertAdjacentText('beforebegin', ' ')
  el.replaceWith(span)
}

export function footnoteToBullet(el) {
  const id = el.dataset.refs.slice(1, -1)
  el.className = 'footnote-bullet'
  el.dataset.type = 'footnote'
  el.innerText = id

  const source = document.querySelector(`[data-identifier='footnote:${id}']`)
  if (!source) {
    el.remove()
    return
  }

  const url = extractUrl(source)
  if (url) {
    el.dataset.url = url
    el.classList.add('url')
    el.setAttribute('data-tooltip', url)
  } else {
    el.removeAttribute('data-url')
    el.classList.remove('url')
    el.setAttribute('data-tooltip', source.textContent.trim())
  }
}