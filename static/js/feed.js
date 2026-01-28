document.addEventListener('DOMContentLoaded', function() {
    const agreeButtons = document.querySelectorAll('.agree-btn');
    const disagreeButtons = document.querySelectorAll('.disagree-btn');

    agreeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const complaintId = this.getAttribute('data-id');
            vote(complaintId, 'agree');
        });
    });

    disagreeButtons.forEach(button => {
        button.addEventListener('click', function() {
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
                const countSpan = document.querySelector(`.${type}-btn[data-id="${complaintId}"] .${type}-count`);
                countSpan.textContent = data[`${type}_count`];
                // Optionally, reorder the cards based on new counts
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
