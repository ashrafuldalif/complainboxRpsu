document.addEventListener('DOMContentLoaded', function() {
    // Dark mode toggle functionality
    const themeToggle = document.getElementById('themeToggle');
    const body = document.body;

    // Function to set theme
    function setTheme(theme) {
        if (theme === 'dark') {
            body.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            body.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
        }
    }

    // Function to toggle theme
    function toggleTheme() {
        const currentTheme = body.getAttribute('data-theme');
        if (currentTheme === 'dark') {
            setTheme('light');
        } else {
            setTheme('dark');
        }
    }

    // Load saved theme on page load
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        setTheme('dark');
    }

    // Add click event to theme toggle button
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    const form = document.getElementById('complaintForm');
    const successMessage = document.getElementById('successMessage');
    const submitAnotherBtn = document.getElementById('submitAnother');

    if (form) {
        // Handle form submission with AJAX
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = new FormData(form);
            const submitBtn = form.querySelector('.submit-btn');
            
            // Disable button during submission
            submitBtn.disabled = true;
            submitBtn.style.opacity = '0.6';
            submitBtn.querySelector('span').textContent = 'Submitting...';

            fetch('/submit', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message
                    form.style.display = 'none';
                    successMessage.classList.add('show');
                    document.getElementById('referenceId').textContent = data.reference_id;

                    // Scroll to top
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                } else {
                    alert('Error: ' + data.message);
                    submitBtn.disabled = false;
                    submitBtn.style.opacity = '1';
                    submitBtn.querySelector('span').textContent = 'Submit Complaint';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
                submitBtn.disabled = false;
                submitBtn.style.opacity = '1';
                submitBtn.querySelector('span').textContent = 'Submit Complaint';
            });
        });

        // Submit another button
        if (submitAnotherBtn) {
            submitAnotherBtn.addEventListener('click', function() {
                form.reset();
                form.style.display = 'block';
                successMessage.classList.remove('show');
                
                const submitBtn = form.querySelector('.submit-btn');
                submitBtn.disabled = false;
                submitBtn.style.opacity = '1';
                submitBtn.querySelector('span').textContent = 'Submit Complaint';
                
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }

        // Add real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.required && !this.value.trim()) {
                    this.style.borderColor = '#ef4444';
                } else {
                    this.style.borderColor = '';
                }
            });

            input.addEventListener('input', function() {
                if (this.style.borderColor === 'rgb(239, 68, 68)') {
                    if (this.value.trim()) {
                        this.style.borderColor = '';
                    }
                }
            });
        });

        // Email validation
        const emailInput = document.getElementById('email');
        if (emailInput) {
            emailInput.addEventListener('blur', function() {
                const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (this.value && !emailPattern.test(this.value)) {
                    this.style.borderColor = '#ef4444';
                }
            });
        }

        // Character counter for textarea
        const complaintTextarea = document.getElementById('complaint');
        if (complaintTextarea) {
            const charCountDisplay = complaintTextarea.parentElement.querySelector('.char-count');
            
            function updateCharCount() {
                const count = complaintTextarea.value.length;
                charCountDisplay.textContent = `${count} characters`;
                
                if (count < 20) {
                    charCountDisplay.style.color = '#ef4444';
                } else if (count < 50) {
                    charCountDisplay.style.color = '#f59e0b';
                } else {
                    charCountDisplay.style.color = '#10b981';
                }
            }

            complaintTextarea.addEventListener('input', updateCharCount);
            updateCharCount();
        }
    }

    // Auth tabs
    const loginTab = document.getElementById('loginTab');
    const registerTab = document.getElementById('registerTab');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    if (loginTab && registerTab) {
        loginTab.addEventListener('click', function() {
            loginTab.classList.add('active');
            registerTab.classList.remove('active');
            loginForm.style.display = 'block';
            registerForm.style.display = 'none';
        });

        registerTab.addEventListener('click', function() {
            registerTab.classList.add('active');
            loginTab.classList.remove('active');
            registerForm.style.display = 'block';
            loginForm.style.display = 'none';
        });
    }

    // Auth form submissions
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            fetch('/login', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/feed';
                } else {
                    alert(data.message);
                }
            })
            .catch(err => {
                console.error(err);
                alert('Login failed');
            });
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            fetch('/register', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/feed';
                } else {
                    alert(data.message);
                }
            })
            .catch(err => {
                console.error(err);
                alert('Registration failed');
            });
        });
    }
});
