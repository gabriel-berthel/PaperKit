export function maskTags(text) {
  const div = document.createElement('div');
  div.innerHTML = text;
  div.querySelectorAll('*').forEach(el => el.remove());
  return div.textContent;
}

export function stripTags(text) {
  return text.replace(/<[^>]*>/g, '').trim();
}

export function extractUrl(el) {
  const anchor = el.querySelector('[data-type="a-link"][data-url]')
  if (anchor) return anchor.dataset.url

  const text = el.textContent.trim()
  try {
    const url = new URL(text)
    if (url.protocol === 'http:' || url.protocol === 'https:') return url.href
  } catch {}

  return null
}