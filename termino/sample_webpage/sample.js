document.querySelectorAll('.terminalButton').forEach(button => {
    button.addEventListener('click', function() {
        const scriptName = this.getAttribute('data-script');
        // Include the full URL pointing to the Flask app
        const url = `http://localhost:5000/terminal/${scriptName}`; // Assuming Flask is running on localhost port 5000
        window.open(url, 'Terminal', 'width=600,height=400');
    });
});

// Close the modal when clicking on the overlay
document.getElementById('overlay').addEventListener('click', function() {
    this.style.display = 'none';
    document.getElementById('terminalContainer').style.display = 'none';
});
