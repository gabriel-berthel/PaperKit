import {resolveRefs} from "../dom/prefetch.js";

/**
 * actions/medias.js
 *
 * Floating, draggable, minimisable media popups.
 * One popup per unique set of refs (keyed by sorted ref strings).
 */

// ── State ─────────────────────────────────────────────────────────────────────

const registry   = new Map(); // key → popup element
let   zCounter   = 1000;
let   popupOffset = 0;

// ── Z-order / focus ───────────────────────────────────────────────────────────

function bringToFront(popup) {
  document.querySelectorAll(".media-popup.active")
    .forEach((el) => el.classList.remove("active"));
  popup.classList.add("active");
  popup.style.zIndex = ++zCounter;
}

// ── Registry key ──────────────────────────────────────────────────────────────

function getKey(items) {
  return items.map(({ ref }) => ref).sort().join("|");
}

// ── Popup positioning ─────────────────────────────────────────────────────────

const POPUP_WIDTH  = 440;
const POPUP_HEIGHT = 320;
const MAX_OFFSET   = 180;
const OFFSET_STEP  = 24;

function getPosition(rect) {
  const offset  = popupOffset;
  popupOffset   = (popupOffset + OFFSET_STEP) % MAX_OFFSET;

  return {
    left: Math.min(
      window.scrollX + rect.left + offset,
      window.scrollX + window.innerWidth  - POPUP_WIDTH  - 20,
    ),
    top: Math.min(
      window.scrollY + rect.top  + offset,
      window.scrollY + window.innerHeight - POPUP_HEIGHT - 20,
    ),
  };
}

// ── Drag ──────────────────────────────────────────────────────────────────────

function makeDraggable(popup, handle) {
  handle.addEventListener("mousedown", (e) => {
    if (e.button !== 0) {return;}
    e.preventDefault();
    bringToFront(popup);

    const rect    = popup.getBoundingClientRect();
    const offsetX = e.clientX - rect.left;
    const offsetY = e.clientY - rect.top;

    const onMove = (e) => {
      popup.style.left = `${window.scrollX + e.clientX - offsetX}px`;
      popup.style.top  = `${window.scrollY + e.clientY - offsetY}px`;
    };
    const onUp = () => {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup",   onUp);
    };

    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup",   onUp);
  });
}

// ── Dock (minimised tray) ─────────────────────────────────────────────────────

function getDock() {
  return (
    document.querySelector(".media-popup-dock") ??
    Object.assign(document.body.appendChild(document.createElement("div")), {
      className: "media-popup-dock",
    })
  );
}

function minimizePopup(popup, titleText) {
  if (popup._dockItem) {return;}
  popup.classList.add("minimized");

  const item     = document.createElement("button");
  item.className = "media-popup-dock-item";
  item.textContent = titleText;
  item.onclick   = () => restorePopup(popup);

  popup._dockItem = item;
  getDock().appendChild(item);
}

function restorePopup(popup) {
  popup.classList.remove("minimized");
  if (popup._dockItem) {
    popup._dockItem.remove();
    popup._dockItem = null;
  }
  bringToFront(popup);
}

// ── Build popup DOM ───────────────────────────────────────────────────────────

function buildHeader(popup, items, key) {
  const header = document.createElement("div");
  header.className = "media-popup-header";

  const title       = document.createElement("span");
  title.className   = "media-popup-title";
  title.textContent = items.map(({ identifier }) => identifier).join(", ");

  const actions = document.createElement("div");
  actions.className = "media-popup-actions";

  const minimizeBtn       = document.createElement("button");
  minimizeBtn.className   = "media-popup-minimize";
  minimizeBtn.innerHTML   = "—";
  minimizeBtn.title       = "Minimize";
  minimizeBtn.addEventListener("click", () => minimizePopup(popup, title.textContent));

  const closeBtn       = document.createElement("button");
  closeBtn.className   = "media-popup-close";
  closeBtn.innerHTML   = "×";
  closeBtn.title       = "Close";
  closeBtn.addEventListener("click", () => {
    popup.classList.add("closing");
    popup.addEventListener("animationend", () => {
      registry.delete(key);
      popup._dockItem?.remove();
      popup.remove();
    }, { once: true });
  });

  actions.append(minimizeBtn, closeBtn);
  header.append(title, actions);
  return header;
}

function buildBody(items) {
  const body       = document.createElement("div");
  body.className   = "media-popup-body";

  for (const { identifier, caption } of items) {
    const figure       = document.createElement("figure");
    figure.className   = "media-popup-figure";

    const img     = document.createElement("img");
    img.className = "media-popup-img";
    img.src       = `/media/${identifier}.png`;
    img.alt       = identifier;

    const cap         = document.createElement("figcaption");
    cap.className     = "media-popup-caption";
    cap.innerHTML     = caption;

    figure.append(img, cap);
    body.appendChild(figure);
  }

  return body;
}

function createPopup(span, items) {
  const key      = getKey(items);
  const existing = registry.get(key);
  if (existing) {
    restorePopup(existing);
    return;
  }

  const popup       = document.createElement("div");
  popup.className   = "media-popup";
  popup.dataset.popupKey = key;
  registry.set(key, popup);

  const header = buildHeader(popup, items, key);
  const body   = buildBody(items);
  popup.append(header, body);

  const pos    = getPosition(span.getBoundingClientRect());
  popup.style.left = `${pos.left}px`;
  popup.style.top  = `${pos.top}px`;

  document.body.appendChild(popup);
  bringToFront(popup);
  makeDraggable(popup, header);

  popup.addEventListener("mousedown", () => bringToFront(popup));
}

// ── Init ──────────────────────────────────────────────────────────────────────

const MEDIA_SPAN_SELECTOR =
  'span.text-ref[data-type="table"], span.text-ref[data-type="figure"]';

export function initMediaPopup() {
  document.getElementById("app-content").addEventListener("click", (e) => {
    const span = e.target.closest(MEDIA_SPAN_SELECTOR);
    if (!span) {return;}
    if (!window.getSelection().isCollapsed) {return;}

    const items = resolveRefs(span);
    if (!items.length) {return;}

    createPopup(span, items);
  });
}