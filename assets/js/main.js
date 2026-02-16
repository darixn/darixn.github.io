/* ============================================================
   darian@security — Shared JavaScript
   ============================================================ */

// Mobile menu toggle
function toggleMobileMenu() {
    document.querySelector('.nav-links').classList.toggle('active');
}

// Close mobile menu on link click
document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', () => {
        document.querySelector('.nav-links').classList.remove('active');
    });
});

// Header opacity on scroll
window.addEventListener('scroll', () => {
    const header = document.querySelector('.header');
    header.style.background = window.scrollY > 50
        ? 'rgba(0, 43, 54, 0.98)'
        : 'rgba(0, 43, 54, 0.95)';
});

// Scroll-triggered animations
const observer = new IntersectionObserver(
    entries => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); }),
    { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
);
document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));

// Staggered card animations
function staggerCards(selector) {
    document.querySelectorAll(selector).forEach((el, i) => {
        el.style.animationDelay = `${i * 0.1}s`;
    });
}
staggerCards('.card');
staggerCards('.skill-category');
staggerCards('.blog-card');
staggerCards('.contact-item');

// Highlight current page in nav
(function highlightNav() {
    const path = window.location.pathname;
    document.querySelectorAll('.nav-links a').forEach(link => {
        const href = link.getAttribute('href');
        // Match exact page or index
        if (
            (href === 'index.html' && (path.endsWith('/') || path.endsWith('index.html'))) ||
            (href !== 'index.html' && path.endsWith(href))
        ) {
            link.classList.add('active');
        }
    });
})();

// Random terminal glitch effect
setInterval(() => {
    document.querySelectorAll('.command, .terminal-bright').forEach(el => {
        if (Math.random() < 0.01) {
            el.style.textShadow = '2px 0 #ff00ff, -2px 0 #00ffff';
            setTimeout(() => { el.style.textShadow = 'none'; }, 100);
        }
    });
}, 5000);
