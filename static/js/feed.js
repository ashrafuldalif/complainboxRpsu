document.addEventListener('DOMContentLoaded', function () {
    const agreeButtons = document.querySelectorAll('.agree-btn');
    const disagreeButtons = document.querySelectorAll('.disagree-btn');

    agreeButtons.forEach(button => {
        button.addEventListener('click', function () {
            const complaintId = this.getAttribute('data-id');
            vote(complaintId, 'agree');
        });
    });

    disagreeButtons.forEach(button => {
        button.addEventListener('click', function () {
            const complaintId = this.getAttribute('data-id');
            vote(complaintId, 'disagree');
        });
    });

    function vote(complaintId, type) {
        fetch(`/api/complaint/${complaintId}/${type}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update both counts
                    const agreeBtn = document.querySelector(`.agree-btn[data-id="${complaintId}"]`);
                    const disagreeBtn = document.querySelector(`.disagree-btn[data-id="${complaintId}"]`);

                    agreeBtn.querySelector('.agree-count').textContent = data.agree_count;
                    disagreeBtn.querySelector('.disagree-count').textContent = data.disagree_count;

                    // Update active/voted state
                    agreeBtn.classList.toggle('voted', data.user_vote === 'agree');
                    disagreeBtn.classList.toggle('voted', data.user_vote === 'disagree');

                    reorderCards();
                } else {
                    alert('Error updating vote: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while voting.');
            });
    }

    function reorderCards() {
        const feed = document.getElementById('complaints-feed');
        const cards = Array.from(feed.children);

        cards.sort((a, b) => {
            const aAgree = parseInt(a.querySelector('.agree-count').textContent);
            const bAgree = parseInt(b.querySelector('.agree-count').textContent);
            return bAgree - aAgree; // Descending order
        });

        cards.forEach(card => feed.appendChild(card));
    }
});
