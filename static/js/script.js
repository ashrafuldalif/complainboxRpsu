document.addEventListener('DOMContentLoaded', function () {

    // ─── Dark Mode ───────────────────────────────────────────────────────────
    const themeToggle = document.getElementById('themeToggle');
    const body = document.body;

    function setTheme(theme) {
        if (theme === 'dark') {
            body.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            body.removeAttribute('data-theme');
            localStorage.setItem('theme', 'light');
        }
    }

    function toggleTheme() {
        setTheme(body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
    }

    // Apply saved theme immediately (no flash)
    if (localStorage.getItem('theme') === 'dark') setTheme('dark');
    if (themeToggle) themeToggle.addEventListener('click', toggleTheme);

    // ─── Complaint Form (index.html only) ────────────────────────────────────
    const form = document.getElementById('complaintForm');
    if (!form) return;

    const successMessage = document.getElementById('successMessage');
    const submitAnotherBtn = document.getElementById('submitAnother');
    const submitBtn = form.querySelector('.submit-btn');

    // AJAX submit
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        submitBtn.disabled = true;
        submitBtn.style.opacity = '0.6';
        submitBtn.querySelector('span').textContent = 'Submitting...';

        fetch('/submit', { method: 'POST', body: new FormData(form) })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    form.style.display = 'none';
                    successMessage.classList.add('show');
                    document.getElementById('referenceId').textContent = data.reference_id;
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                } else {
                    alert('Error: ' + data.message);
                    resetSubmitBtn();
                }
            })
            .catch(() => {
                alert('An error occurred. Please try again.');
                resetSubmitBtn();
            });
    });

    function resetSubmitBtn() {
        submitBtn.disabled = false;
        submitBtn.style.opacity = '1';
        submitBtn.querySelector('span').textContent = 'Submit Complaint';
    }

    // Submit another complaint
    if (submitAnotherBtn) {
        submitAnotherBtn.addEventListener('click', function () {
            form.reset();
            form.style.display = 'block';
            successMessage.classList.remove('show');
            resetSubmitBtn();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // Real-time required field validation (red border on blur, clears on input)
    form.querySelectorAll('input, select, textarea').forEach(input => {
        input.addEventListener('blur', function () {
            this.style.borderColor = (this.required && !this.value.trim()) ? '#ef4444' : '';
        });
        input.addEventListener('input', function () {
            if (this.style.borderColor === 'rgb(239, 68, 68)' && this.value.trim()) {
                this.style.borderColor = '';
            }
        });
    });

    // Email format check
    const emailInput = document.getElementById('email');
    if (emailInput) {
        emailInput.addEventListener('blur', function () {
            const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.value);
            if (this.value && !valid) this.style.borderColor = '#ef4444';
        });
    }

    // Character counter for complaint textarea
    const complaintTextarea = document.getElementById('complaint');
    if (complaintTextarea) {
        const charCountDisplay = complaintTextarea.parentElement.querySelector('.char-count');
        function updateCharCount() {
            const count = complaintTextarea.value.length;
            charCountDisplay.textContent = `${count} characters`;
            charCountDisplay.style.color = count < 20 ? '#ef4444' : count < 50 ? '#f59e0b' : '#10b981';
        }
        complaintTextarea.addEventListener('input', updateCharCount);
        updateCharCount();
    }

});
