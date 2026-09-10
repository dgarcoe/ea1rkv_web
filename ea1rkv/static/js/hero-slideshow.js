(() => {
    const hero = document.querySelector('.club-hero');
    if (!hero) return;
    const slides = [...hero.querySelectorAll('.hero-slide')];
    const credits = [...hero.querySelectorAll('.hero-slide-credit')];
    const controls = hero.querySelector('.hero-controls');
    if (slides.length < 2 || !controls) return;
    controls.hidden = false;
    const toggle = controls.querySelector('[data-hero-toggle]');
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let paused = reducedMotion.matches;
    let current = 0;
    let timer;
    function show(index) {
        current = (index + slides.length) % slides.length;
        slides.forEach((slide, i) => { slide.hidden = i !== current; });
        credits.forEach((credit, i) => { credit.hidden = i !== current; });
    }
    function schedule() {
        clearInterval(timer);
        toggle.textContent = paused ? 'Reanudar' : 'Pausar';
        if (!paused && !document.hidden && !hero.matches(':hover') && !hero.contains(document.activeElement)) {
            timer = setInterval(() => show(current + 1), 6000);
        }
    }
    toggle.addEventListener('click', () => { paused = !paused; schedule(); });
    controls.querySelector('[data-hero-prev]').addEventListener('click', () => { show(current - 1); schedule(); });
    controls.querySelector('[data-hero-next]').addEventListener('click', () => { show(current + 1); schedule(); });
    hero.addEventListener('mouseenter', schedule);
    hero.addEventListener('mouseleave', schedule);
    hero.addEventListener('focusin', schedule);
    hero.addEventListener('focusout', () => setTimeout(schedule, 0));
    document.addEventListener('visibilitychange', schedule);
    reducedMotion.addEventListener('change', () => { paused = reducedMotion.matches; schedule(); });
    schedule();
})();
