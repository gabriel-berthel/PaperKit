import {push} from "./snapshots.js";

// ── Selectors ─────────────────────────────────────────────────────────────────

/**
 * Builds a CSS attribute selector string from one or more data-type values.
 *   typeSelector("paragraph", "bullet") → '[data-type="paragraph"],[data-type="bullet"]'
 */
export function typeSelector(...types) {
  return types.map((t) => `[data-type="${t}"]`).join(",");
}

// ── Node helpers ──────────────────────────────────────────────────────────────

/**
 * Returns the element for a node: if the node is a text node, returns its
 * parent element; otherwise returns the node itself.
 */
export function resolveElement(node) {
  return node?.nodeType === Node.TEXT_NODE ? node.parentElement : node;
}

// ── Shared actions ────────────────────────────────────────────────────────────

/**
 * Removes an element from the DOM and snapshots the change.
 * Used by both actions/blocks.js and actions/spans.js.
 */
export function removeEl(el) {
  el.remove();
  push();
}

/**
 * Creates a <p> element with the given data-type and optional HTML content.
 */
export function makeDataTypeEl(type, html = "") {
  const el = document.createElement("p");
  el.dataset.type = type;
  if (html) {el.innerHTML = html;}
  return el;
}