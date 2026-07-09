function freezeUI() {
  document.getElementById("loading-overlay")?.classList.add("show");
}

function unfreezeUI() {
  document.getElementById("loading-overlay")?.classList.remove("show");
}

export async function withUI(fn) {
  freezeUI();
  try {
    return await fn();
  } catch (err) {
    alert(err);
    throw err;
  } finally {
    unfreezeUI();
  }
}