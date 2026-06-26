import {withUI} from '../dom/ui_freeze.js';
import {fetchAudio} from '../api/tts.js';

export async function exportAudio() {
  const btn = document.querySelector('#export-tts-btn');
  const originalLabel = btn?.querySelector('.fab-label');

  function setLabel(text) {
    if (originalLabel) originalLabel.textContent = text;
  }

  try {
    // 1. Build the full script
    setLabel('Reading…');
    const script = elements
      .map(el => speechify(el))
      .filter(Boolean)
      .join('\n\n');

    if (!script.trim()) {
      alert('Nothing to export.');
      setLabel('Export');
      return;
    }

    // 2. Fetch audio — already a blob URL
    setLabel('Generating…');
    const blobUrl = await withUI(() => fetchAudio(script))

    // 3. Trigger save dialog
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = 'export.mp3';
    a.click();

    setLabel('Export');
  } catch (err) {
    console.error('Export failed:', err);
    setLabel('Error');
    setTimeout(() => setLabel('Export'), 3000);
  }
}
