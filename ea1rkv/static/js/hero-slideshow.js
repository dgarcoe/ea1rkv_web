(() => {
    const hero = document.querySelector('.club-hero');
    if (!hero) return;
    const slides = [...hero.querySelectorAll('.hero-slide')];
    const credits = [...hero.querySelectorAll('.hero-slide-credit')];
    if (slides.length < 2) return;
    let current = 0;
    setInterval(() => {
        current = (current + 1) % slides.length;
        slides.forEach((slide, i) => { slide.hidden = i !== current; });
        credits.forEach((credit, i) => { credit.hidden = i !== current; });
    }, 6000);
})();
