const menuToggler = () => {
  const toggle = document.querySelector('.page-header-menu__toggle')

  if (!toggle) {
    return
  }

  toggle.onclick = (e) => {
    const el = e.target.closest('.page-header-menu')
    el?.classList.toggle('show')
    document.documentElement.classList[[...el?.classList].includes('show') ? 'add' : 'remove'](
      'open-menu'
    )
  }

  window.addEventListener('click', (e) => {
    if (e.target.closest('.page-header-links__link')) {
      e.target.closest('.page-header-menu')?.classList.remove('show')
    }
  })
}

window.addEventListener("load", () => {
  menuToggler();
});
