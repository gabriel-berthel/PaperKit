import {state} from "../state.js";
import {push} from "../dom/snapshots.js";

// ── Toggle ────────────────────────────────────────────────────────────────────

function toggleEdit() {
  const btn     = document.getElementById("edit-btn");
  const content = document.getElementById("app-content");
  const label   = btn.querySelector(".fab-label");
  const icon    = btn.querySelector(".fab-icon");

  if (!state.editor) {
    state.editor = new MediumEditor(content, {
      toolbar: { buttons: ["bold", "italic", "underline"] },
    });
    content.classList.add("editing");
    btn.classList.add("active");
    label.textContent = "Done";
    icon.textContent  = "✓";
  } else {
    state.editor.destroy();
    state.editor = null;
    content.classList.remove("editing");
    btn.classList.remove("active");
    label.textContent = "Edit";
    icon.textContent  = "✏️";
    push();
  }
}

window.toggleEdit = toggleEdit;