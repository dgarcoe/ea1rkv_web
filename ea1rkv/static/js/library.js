(() => {
  const dialog = document.querySelector('.library-dialog');
  const links = Array.from(document.querySelectorAll('[data-library-image]'));
  if (!dialog || !dialog.showModal || !links.length) return;
  let index = 0;
  let opener;
  const show = (next) => {
    index = (next + links.length) % links.length;
    dialog.querySelector('img').src = links[index].href;
    dialog.querySelector('img').alt = links[index].dataset.title;
    dialog.querySelector('figcaption').textContent = links[index].dataset.title;
  };
  links.forEach((link, i) => link.addEventListener('click', (event) => {
    if (event.ctrlKey || event.metaKey || event.shiftKey) return;
    event.preventDefault(); opener = link; show(i); dialog.showModal();
  }));
  dialog.querySelector('[data-close]').onclick = () => dialog.close();
  dialog.querySelector('[data-prev]').onclick = () => show(index - 1);
  dialog.querySelector('[data-next]').onclick = () => show(index + 1);
  dialog.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft') { event.preventDefault(); show(index - 1); }
    if (event.key === 'ArrowRight') { event.preventDefault(); show(index + 1); }
  });
  dialog.addEventListener('close', () => { if (opener) opener.focus(); });
})();
