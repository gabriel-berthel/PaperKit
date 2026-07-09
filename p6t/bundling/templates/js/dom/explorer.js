const typeConfig = {
  heading: { label: el => el.textContent.trim() },
  formula: { label: () => '[FORMULA]' },
  code:    { label: () => '[CODE]' },
};

const defaultLabel = el => el.textContent.trim().split(/\s+/).slice(0, 10).join(' ') + '…';

export function initExplorer() {
  const appContent = document.getElementById('app-content');
  const explorerSection = document.getElementById('explorer-content');

  function rebuildExplorer() {
    explorerSection.innerHTML = '';
    appContent.querySelectorAll(':scope > *').forEach(block => {
      const type = block.dataset.type;
      const cfg = typeConfig[type];
      const label = cfg ? cfg.label(block) : defaultLabel(block);

      const anchor = document.createElement('a');
      anchor.href = '#' + block.id;
      anchor.textContent = label;
      anchor.dataset.type = type;
      anchor.addEventListener('click', e => {
        e.preventDefault();
        explorerSection.querySelectorAll('a').forEach(a => a.classList.remove('active'));
        anchor.classList.add('active');
        block.scrollIntoView({ behavior: 'smooth',  block: 'start'});
      });
      explorerSection.appendChild(anchor);
    });
  }

  const observer = new MutationObserver(rebuildExplorer);
  observer.observe(appContent, { childList: true, subtree: true });
  rebuildExplorer();
}