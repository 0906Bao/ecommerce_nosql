document.querySelectorAll('[data-password-toggle]').forEach(button => {
    const input = document.getElementById(button.getAttribute('aria-controls'));
    const icon = button.querySelector('i');
    const showLabel = button.getAttribute('aria-label');

    button.addEventListener('click', () => {
        const show = input.type === 'password';
        input.type = show ? 'text' : 'password';
        icon.classList.toggle('fa-eye', !show);
        icon.classList.toggle('fa-eye-slash', show);
        button.setAttribute('aria-label', show ? showLabel.replace('Hiện', 'Ẩn') : showLabel);
    });
});
