document.addEventListener('DOMContentLoaded', function () {
    const registerForm = document.getElementById('registerForm');
    if (!registerForm) return;

    registerForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const name = document.getElementById('name').value;
        const studentId = document.getElementById('student_id').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;
        const errorMessage = document.getElementById('errorMessage');

        // Validate email domain
        if (!email.endsWith('@rpsu.edu.bd')) {
            errorMessage.textContent = 'Please use a valid @rpsu.edu.bd email address';
            errorMessage.style.display = 'block';
            return;
        }

        // Validate password match
        if (password !== confirmPassword) {
            errorMessage.textContent = 'Passwords do not match';
            errorMessage.style.display = 'block';
            return;
        }

        errorMessage.style.display = 'none';

        fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                name,
                student_id: studentId,
                email,
                password,
                confirm_password: confirmPassword
            })
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
