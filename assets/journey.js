/* Skipi journey: мягкое появление элементов по мере движения.
   Ванильный JS, без зависимостей; уважает prefers-reduced-motion. */
(function () {
    "use strict";
    var els = document.querySelectorAll(".reveal");
    var reduced = window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!("IntersectionObserver" in window) || reduced) {
        els.forEach(function (el) { el.classList.add("in"); });
        return;
    }
    var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
            if (en.isIntersecting) {
                en.target.classList.add("in");
                io.unobserve(en.target);
            }
        });
    }, { threshold: 0.25 });
    els.forEach(function (el) { io.observe(el); });
})();
