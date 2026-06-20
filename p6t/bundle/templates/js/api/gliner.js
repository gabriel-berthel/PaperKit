import { request, ENDPOINTS } from "./utils.js";

const STRIP_SELECTORS = [
  'span[data-type="inline-maths"]',
  'span[data-type="reference"]',
  'span[data-type="footnote"]',
  'mark[data-type="entity"]',
  'script',
  'style',
];

function extractDocumentText(root) {
  const clone = root.cloneNode(true);
  for (const sel of STRIP_SELECTORS) {
    clone.querySelectorAll(sel).forEach(n => n.remove());
  }
  return Array.from(clone.querySelectorAll('p'))
    .map(p => p.textContent.trim())
    .filter(Boolean)
    .join('\n');
}

export async function glinerMatchesFetch(terms) {
  if (!terms.length) return {};

  const root = document.querySelector('#app-content');
  if (!root) return {};

  const text = extractDocumentText(root);

  const res = await request(ENDPOINTS.GLINER_PROBE, {
    method: "POST",
    payload: { text, targets: terms }
  });


  if (!res.ok) throw new Error(`Probe request failed: ${res.status}`);

  const data = await res.json();
  
  return data; // expected: { [term]: string[] }
}