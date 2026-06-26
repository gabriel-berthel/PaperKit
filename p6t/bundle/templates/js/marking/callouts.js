const CALLOUT_PATTERN = /^(Definition|Theorem|Lemma|Proposition|Corollary|Table|Figure|Algorithm)\s*[\d.]*\s*:?/i;

function applyCalloutStyling(el) {
  const text = el.textContent.trim();
  const match = text.match(CALLOUT_PATTERN);
  if (match) {
    el.classList.add('callout');
    el.dataset.calloutType = match[1].toLowerCase();
  } else {
    el.classList.remove('callout');
    delete el.dataset.calloutType;
  }
}
function scanExistingParagraphs(root) {
    root.querySelectorAll('p').forEach(applyCalloutStyling);
}

function observeNewParagraphs(root) {
    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {
                if (node.nodeType !== Node.ELEMENT_NODE) continue;
                if (node.tagName === 'P') {
                    applyCalloutStyling(node);
                } else {
                    node.querySelectorAll?.('p').forEach(applyCalloutStyling);
                }
            }
        }
    });
    observer.observe(root, { childList: true, subtree: true });
    return observer;
}

export function initCallouts(rootSelector = '#app-content') {
    const root = document.querySelector(rootSelector);
    if (!root) {
        console.warn(`initCallouts: no element found for selector "${rootSelector}"`);
        return null;
    }
    scanExistingParagraphs(root);
    return observeNewParagraphs(root);
}