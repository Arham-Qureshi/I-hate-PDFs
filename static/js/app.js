document.addEventListener('DOMContentLoaded', () => {
    // bye menu
    const toggle = document.getElementById('mobile-menu-toggle');
    const menu = document.getElementById('mobile-menu');

    if (toggle && menu) {
        toggle.addEventListener('click', () => {
            const isOpen = !menu.classList.contains('hidden');
            if (isOpen) {
                menu.classList.add('hidden');
                menu.classList.remove('flex');
                document.body.style.overflow = '';
            } else {
                menu.classList.remove('hidden');
                menu.classList.add('flex');
                document.body.style.overflow = 'hidden';
            }
        });

        menu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                menu.classList.add('hidden');
                menu.classList.remove('flex');
                document.body.style.overflow = '';
            });
        });
    }

    // fade out flashes
    const flashContainer = document.getElementById('flash-messages');
    if (flashContainer) {
        setTimeout(() => {
            flashContainer.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            flashContainer.style.opacity = '0';
            flashContainer.style.transform = 'translateY(-20px) translateX(-50%)';
            setTimeout(() => flashContainer.remove(), 400);
        }, 4000);
    }

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', (e) => {
            const target = document.querySelector(anchor.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    const themes = [
        { id: 'light', icon: '☀️', name: 'Light' },
        { id: 'dark', icon: '🌙', name: 'Dark' },
        { id: 'retro', icon: '📻', name: 'Retro' },
        { id: 'neon', icon: '⚡', name: 'Neon' }
    ];

    let currentThemeIdx = themes.findIndex(t => t.id === (localStorage.getItem('theme') || 'light'));
    if (currentThemeIdx === -1) currentThemeIdx = 0;

    const applyThemeUX = (idx) => {
        const theme = themes[idx];
        document.documentElement.setAttribute('data-theme', theme.id);
        localStorage.setItem('theme', theme.id);

        const desktopIcon = document.getElementById('theme-icon');
        const desktopName = document.getElementById('theme-name');
        if (desktopIcon) desktopIcon.textContent = theme.icon;
        if (desktopName) desktopName.textContent = theme.name;

        const mobileIcon = document.getElementById('mobile-theme-icon');
        if (mobileIcon) mobileIcon.textContent = theme.icon;
    };

    applyThemeUX(currentThemeIdx);

    const switchTheme = () => {
        currentThemeIdx = (currentThemeIdx + 1) % themes.length;
        applyThemeUX(currentThemeIdx);
    };

    const dBtn = document.getElementById('theme-toggle');
    const mBtn = document.getElementById('mobile-theme-toggle');
    if (dBtn) dBtn.addEventListener('click', switchTheme);
    if (mBtn) mBtn.addEventListener('click', switchTheme);

    document.querySelectorAll('.playful, .wobble-card').forEach(el => {
        const randomRot = (Math.random() * 4 - 2).toFixed(2); // -2 to 2 deg
        el.style.transform = `rotate(${randomRot}deg)`;

        el.addEventListener('mouseenter', () => {
            el.style.transform = `rotate(${(Math.random() * 2 - 1).toFixed(2)}deg) translateY(-4px)`;
        });
        el.addEventListener('mouseleave', () => {
            el.style.transform = `rotate(${randomRot}deg)`;
        });
    });
});