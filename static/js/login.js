document.addEventListener('DOMContentLoaded', function () {
    const loginForm = document.getElementById('loginForm');
    if (!loginForm) return;

    loginForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const errorMessage = document.getElementById('errorMessage');

        // Validate email domain
        if (!email.endsWith('@rpsu.edu.bd')) {
            errorMessage.textContent = 'Please use a valid @rpsu.edu.bd email address';
            errorMessage.style.display = 'block';
            return;
        }

        errorMessage.style.display = 'none';

        fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ email, password })
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/feed';
                } else {
                    errorMessage.textContent = data.message;
                    errorMessage.style.display = 'block';
                }
            })
            .catch(() => {
                errorMessage.textContent = 'An error occurred. Please try again.';
                errorMessage.style.display = 'block';
            });
    });
});
