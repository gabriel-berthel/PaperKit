const TYPES = new Set(['table', 'figure', 'footnote'])

export function resolveRefs(span) {
  const { type, refs: rawRefs } = span.dataset
  if (!TYPES.has(type)) return []

  const refs = rawRefs.slice(1, -1).split(',').map(r => r.trim())
  return refs.flatMap(ref => {
    const identifier = `${type}:${ref}`
    const caption    = document.querySelector(`[data-type="caption"][data-identifier="${identifier}"]`)
    if (!caption) return []
    return [{ ref, identifier, caption: caption.textContent }]
  })
}