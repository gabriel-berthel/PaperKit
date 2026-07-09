let activeMenu = null;

// ── Positioning ───────────────────────────────────────────────────────────────

function positionMenu(wrap, x, y) {
  Object.assign(wrap.style, {
    position: "fixed",
    zIndex:   "99999",
    left:     `${x}px`,
    top:      `${y}px`,
  });

  // Clamp to viewport after paint so dimensions are known.
  requestAnimationFrame(() => {
    const rect = wrap.getBoundingClientRect();
    if (rect.right  > window.innerWidth  - 8) {wrap.style.left = `${x - rect.width}px`;}
    if (rect.bottom > window.innerHeight - 8) {wrap.style.top  = `${y - rect.height}px`;}
  });
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────

function closeMenu() {
  activeMenu?.remove();
  activeMenu = null;
}

function buildMenu(actions, targetEl) {
  const wrap = document.createElement("div");
  wrap.id = "span-context-menu";

  for (const action of actions) {
    const btn = document.createElement("button");
    btn.dataset.action = action.id;
    btn.textContent    = action.label;
    btn.onclick        = async () => {
      await action.run(targetEl);
      closeMenu();
    };
    wrap.appendChild(btn);
  }

  return wrap;
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Opens a context menu.
 * @param {Array<{id:string, label:string, run:function}>} actions
 * @param {Element} targetEl  The DOM element the actions will operate on.
 * @param {number}  x         clientX of the triggering mouse event.
 * @param {number}  y         clientY of the triggering mouse event.
 */
export function openPopupMenu(actions, targetEl, x, y) {
  closeMenu();
  activeMenu = buildMenu(actions, targetEl);
  document.body.appendChild(activeMenu);
  positionMenu(activeMenu, x, y);
}

/**
 * Call once during app init to wire up the global dismiss listeners.
 */
export function initPopupMenu() {
  document.addEventListener("mousedown", (e) => {
    if (!activeMenu?.contains(e.target)) {closeMenu();}
  });
  document.addEventListener("scroll", closeMenu, true);
}