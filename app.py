from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import subprocess
import threading

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

def run_script(client_sid, script_path):
    # Start the subprocess with pipes for stdout and stderr
    proc = subprocess.Popen(['python', script_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    
    # Function to handle output from a stream
    def handle_stream(stream, event_name):
        while True:
            line = stream.readline()
            if line:
                socketio.emit(event_name, {'output': line.strip()}, to=client_sid)
            else:
                break
        stream.close()

    # Use threads to handle stdout and stderr separately
    stdout_thread = threading.Thread(target=handle_stream, args=(proc.stdout, 'script_output'))
    stderr_thread = threading.Thread(target=handle_stream, args=(proc.stderr, 'script_output'))
    stdout_thread.start()
    stderr_thread.start()
    
    # Wait for the threads to finish
    stdout_thread.join()
    stderr_thread.join()

    # Close the process' stdin and wait for it to finish
    proc.stdin.close()
    proc.wait()
    emit('script_output', {'output': '', 'finished': True}, to=client_sid)

@socketio.on('start_script')
def handle_start_script(json):
    client_sid = request.sid
    script_path = json['script_path']
    threading.Thread(target=run_script, args=(client_sid, script_path)).start()

if __name__ == '__main__':
    socketio.run(app, debug=True)
