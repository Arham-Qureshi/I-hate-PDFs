tailwind.config = {
    theme: {
        extend: {
            colors: {
                'hb-bg': 'var(--c-bg)',
                'hb-text': 'var(--c-text)',
                'hb-muted': 'var(--c-muted)',
                'hb-accent': 'var(--c-accent)',
                'hb-secondary': 'var(--c-secondary)',
            },
            fontFamily: {
                'heading': ['Kalam', 'cursive'],
                'body': ['Patrick Hand', 'cursive'],
            },
            fontSize: {
                'sm': ['14px', '1.6'],
                'base': ['16px', '1.6'],
                'lg': ['16px', '1.6'],
                'xl': ['20px', '1.6'],
                '2xl': ['24px', '1.6'],
                '3xl': ['32px', '1.6'],
                '4xl': ['32px', '1.6'],
                '5xl': ['48px', '1.6'],
                '6xl': ['48px', '1.6'],
                '7xl': ['48px', '1.6'],
                '8xl': ['48px', '1.6'],
                '9xl': ['48px', '1.6'],
            }
        },
    },
}

//external theme for tailwind
const savedTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', savedTheme);
