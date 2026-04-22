document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('mobile-menu-toggle');
    const menu = document.getElementById('mobile-menu');

    if (toggle && menu) {
        const setMobileMenu = (open) => {
            menu.classList.toggle('is-open', open);
            toggle.setAttribute('aria-expanded', String(open));
            toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
            document.body.style.overflow = open ? 'hidden' : '';
        };

        toggle.addEventListener('click', () => {
            setMobileMenu(!menu.classList.contains('is-open'));
        });

        menu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => setMobileMenu(false));
        });
    }

    const closeDropdowns = (except = null) => {
        document.querySelectorAll('[data-nav-dropdown]').forEach(dropdown => {
            if (dropdown === except) return;
            dropdown.classList.remove('is-open');
            dropdown.querySelector('[data-nav-dropdown-trigger]')?.setAttribute('aria-expanded', 'false');
        });
    };

    document.querySelectorAll('[data-nav-dropdown]').forEach(dropdown => {
        const trigger = dropdown.querySelector('[data-nav-dropdown-trigger]');
        if (!trigger) return;

        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            const nextOpen = !dropdown.classList.contains('is-open');
            closeDropdowns(dropdown);
            dropdown.classList.toggle('is-open', nextOpen);
            trigger.setAttribute('aria-expanded', String(nextOpen));
        });

        dropdown.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                dropdown.classList.remove('is-open');
                trigger.setAttribute('aria-expanded', 'false');
                trigger.focus();
            }
        });
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('[data-nav-dropdown]')) closeDropdowns();
    });

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
        { id: 'light', icon: 'sun', name: 'Light' },
        { id: 'dark', icon: 'moon', name: 'Dark' },
        { id: 'retro', icon: 'radio', name: 'Retro' },
        { id: 'neon', icon: 'zap', name: 'Neon' }
    ];

    let currentThemeIdx = themes.findIndex(t => t.id === (localStorage.getItem('theme') || 'light'));
    if (currentThemeIdx === -1) currentThemeIdx = 0;

    const applyThemeUX = (idx) => {
        const theme = themes[idx];
        document.documentElement.setAttribute('data-theme', theme.id);
        localStorage.setItem('theme', theme.id);

        const iconHtml = `<i data-lucide="${theme.icon}" class="w-4 h-4 inline-block"></i>`;
        const desktopIcon = document.getElementById('theme-icon');
        const desktopName = document.getElementById('theme-name');
        if (desktopIcon) desktopIcon.innerHTML = iconHtml;
        if (desktopName) desktopName.textContent = theme.name;

        const mobileIcon = document.getElementById('mobile-theme-icon');
        if (mobileIcon) mobileIcon.innerHTML = iconHtml;
        lucide.createIcons();
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
        const randomRot = (Math.random() * 4 - 2).toFixed(2);
        el.style.transform = `rotate(${randomRot}deg)`;

        el.addEventListener('mouseenter', () => {
            el.style.transform = `rotate(${(Math.random() * 2 - 1).toFixed(2)}deg) translateY(-4px)`;
        });
        el.addEventListener('mouseleave', () => {
            el.style.transform = `rotate(${randomRot}deg)`;
        });
    });
});
