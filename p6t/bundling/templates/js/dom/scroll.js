function jumpTo(el) {
  requestAnimationFrame(() => {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}

function flashEl(el, color = '#ffe066') {
  requestAnimationFrame(() => {
    el.style.setProperty('--flash-color', color)
    el.classList.add('flash')
    setTimeout(() => el.classList.remove('flash'), 1200)
  })
}

export function jumpAndFlash(el, color = '#ffe066') {
  jumpTo(el)
  flashEl(el, color)
}