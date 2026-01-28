function getUserLocation() {
    if (!navigator.geolocation) {
        showLocationError("Geolocation is not supported by this browser.");
        return;
    }

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const data = {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                accuracy: position.coords.accuracy
            };

            fetch("/location", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            })
            .then(res => res.json())
            .then(result => {
                console.log("Server response:", result);
                if (result.allowed) {
                    showForm();
                } else {
                    showWarning();
                }
            })
            .catch(err => {
                console.error(err);
                showLocationError("Failed to verify location. Please try again.");
            });
        },
        (error) => {
            console.error("Location error:", error.message);
            showLocationError("Location access denied. Please enable location services to access the complaint box.");
        }
    );
}

function showForm() {
    document.getElementById('locationLoading').style.display = 'none';
    document.getElementById('complaintForm').style.display = 'block';
}

function showWarning() {
    document.getElementById('locationLoading').style.display = 'none';
    document.getElementById('locationWarning').style.display = 'block';

    // Add event listener to retake location button
    const retakeBtn = document.getElementById('retakeLocationBtn');
    if (retakeBtn) {
        retakeBtn.addEventListener('click', function() {
            // Hide warning and show loading
            document.getElementById('locationWarning').style.display = 'none';
            document.getElementById('locationLoading').style.display = 'block';
            // Retake location
            getUserLocation();
        });
    }
}

function showLocationError(message) {
    document.getElementById('locationLoading').style.display = 'none';
    const warningDiv = document.getElementById('locationWarning');
    warningDiv.innerHTML = `
        <div class="warning-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </div>
        <h2>Location Error</h2>
        <p>${message}</p>
    `;
    warningDiv.style.display = 'block';
}

// Call getUserLocation when page loads
document.addEventListener('DOMContentLoaded', function() {
    getUserLocation();
});
