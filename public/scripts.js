document.getElementById('analyze-btn').addEventListener('click', function() {
    const productUrl = document.getElementById('product-url').value;
    const loadingDiv = document.getElementById('loading');
    const loadingText = document.getElementById('loading-text');

    if (!productUrl) {
        alert("Please enter a product URL.");
        return;
    }

    // Show loading indicator
    loadingDiv.style.display = 'block';
    loadingText.textContent = 'Processing your request...';

    // Start the analysis
    fetch(`/analyze?url=${encodeURIComponent(productUrl)}`)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            
            // Start polling for status updates
            const statusInterval = setInterval(() => {
                fetch('/status')
                    .then(response => response.json())
                    .then(statusData => {
                        loadingText.textContent = statusData.status;

                        // If the status is empty, the process is complete
                        if (!statusData.status) {
                            clearInterval(statusInterval);
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching status:', error);
                        clearInterval(statusInterval);
                        alert("Error fetching status.");
                    });
            }, 1000); // Check status every 1 second

            return response.json(); // Return the response to get final data
        })
        .then(data => {
            // Once we receive the final result, display it
            displayResults(data.percentage);
        })
        .catch(error => {
            console.error('Error:', error);
            alert("There was an error processing the request.");
        })
        .finally(() => {
            // Hide loading indicator after processing
            loadingDiv.style.display = 'none';
        });
});

function displayResults(fakeReviewPercentage) {
    const ctx = document.getElementById('fake-review-chart').getContext('2d');
    const percentage = fakeReviewPercentage;

    let color;
    let message;

    if (percentage < 20) {
        color = 'green';
        message = 'Excellent! Most reviews are genuine.';
    } else if (percentage < 50) {
        color = 'yellow';
        message = 'Be cautious. Some reviews may be fake.';
    } else {
        color = 'red';
        message = 'Warning! A large number of reviews may be fake.';
    }

    // Destroy existing chart before creating a new one
    if (window.chart) {
        window.chart.destroy();
    }

    window.chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [percentage, 100 - percentage],
                backgroundColor: [color, '#e0e0e0']
            }],
            labels: ['Fake Reviews', 'Genuine Reviews']
        },
        options: {
            responsive: true,
            cutoutPercentage: 70,
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff', // Change this to your desired label color
                        font: {
                            size: 14 // Change this to adjust font size
                        }
                    }
                }
            },
            animation: {
                animateScale: true
            }
        }
    });

    document.getElementById('message').innerText = message;
    document.getElementById('result').style.display = 'block';
}
