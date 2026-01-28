document.addEventListener('DOMContentLoaded', function() {
    // Handle login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
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

            // Clear previous error
            errorMessage.style.display = 'none';

            // Submit form via AJAX
            fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    email: email,
                    password: password
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Redirect to feed on success
                    window.location.href = '/feed';
                } else {
                    // Show error message
                    errorMessage.textContent = data.message;
                    errorMessage.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                errorMessage.textContent = 'An error occurred. Please try again.';
                errorMessage.style.display = 'block';
            });
        });
    }

    // Handle register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
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

            // Clear previous error
            errorMessage.style.display = 'none';

            // Submit form via AJAX
            fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    name: name,
                    student_id: studentId,
                    email: email,
                    password: password,
                    confirm_password: confirmPassword
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Redirect to feed on success
                    window.location.href = '/feed';
                } else {
                    // Show error message
                    errorMessage.textContent = data.message;
                    errorMessage.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                errorMessage.textContent = 'An error occurred. Please try again.';
                errorMessage.style.display = 'block';
            });
        });
    }
});
