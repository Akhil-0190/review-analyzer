const express = require('express');
const path = require('path');
const { exec } = require('child_process');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static('public'));

const pythonPath = "";
let currentStatus = ''; // Variable to store the current status

// Route for processing reviews
app.get('/analyze', (req, res) => {
    const productUrl = req.query.url;

    console.log(`Analyzing URL: ${productUrl}`); // Log the URL being analyzed
    currentStatus = 'Extracting reviews...'; // Update status
    console.log(currentStatus); // Log status to console

    // Step 1: Execute flipkart_reviews.py with the provided link as an argument
    exec(`${pythonPath} flipkart_reviews.py "${productUrl}"`, (error, stdout, stderr) => {
        if (error) {
            console.error(`Error executing Flipkart script: ${stderr}`);
            currentStatus = ''; // Clear status on error
            return res.status(500).send('Error fetching reviews.'); // Return early on error
        }
        console.log(`Flipkart Reviews Fetched`);

        currentStatus = 'Cleaning reviews...'; // Update status
        console.log(currentStatus); // Log status to console

        // Step 2: Execute reviews_cleaning.py after fetching reviews
        exec(`${pythonPath} reviews_cleaning.py`, (error, stdout, stderr) => {
            if (error) {
                console.error(`Error executing reviews cleaning script: ${stderr}`);
                currentStatus = ''; // Clear status on error
                return res.status(500).send('Error cleaning reviews.'); // Return early on error
            }
            console.log(`Reviews Cleaned`);

            currentStatus = 'Analyzing reviews...'; // Update status
            console.log(currentStatus); // Log status to console

            // Step 3: Execute fake_reviews.py to analyze the cleaned reviews
            exec(`${pythonPath} fake_reviews.py`, (error, stdout, stderr) => {
                if (error) {
                    console.error(`Error executing review analysis script: ${stderr}`);
                    currentStatus = ''; // Clear status on error
                    return res.status(500).send('Error analyzing reviews.'); // Return early on error
                }

                const fakeReviewPercentage = parseFloat(stdout.trim()); // Assuming this outputs the percentage
                currentStatus = ''; // Clear status after completion
                console.log("Finished Analysis")
                res.json({ percentage: fakeReviewPercentage }); // Send the final response once
            });
        });
    });
});

// Route for checking the status
app.get('/status', (req, res) => {
    res.json({ status: currentStatus });
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
