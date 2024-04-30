document.addEventListener('DOMContentLoaded', function() {
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
    var inputArea = document.getElementById('input-area');
    var userInput = document.getElementById('user-input');
    var submitInput = document.getElementById('submit-input');

    document.getElementById('run-button').onclick = function() {
        socket.emit('start_script', { 'script_path': 'projects/day1/main.py' });
        this.style.display = 'none';  // Hide the start button
    };

    socket.on('request_input', function(prompt) {
        document.getElementById('output').textContent += '\n' + prompt;
        userInput.style.display = 'inline';
        submitInput.style.display = 'inline';
        userInput.focus();
    });

    submitInput.onclick = function() {
        var input = userInput.value;
        userInput.value = '';  // Clear the input field
        userInput.style.display = 'none';
        submitInput.style.display = 'none';
        socket.emit('send_input', input);
    };

    socket.on('script_output', function(data) {
        document.getElementById('output').textContent += data.output + '\n';
        if (data.finished) {
            document.getElementById('run-button').style.display = 'inline';  // Show the start button again
        }
    });
});
