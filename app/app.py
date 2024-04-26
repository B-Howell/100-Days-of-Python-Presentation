from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import subprocess
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*')

# Dictionary to keep track of subprocesses
subprocesses = {}
lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

def read_output(proc, sid):
    try:
        while True:
            output = proc.stdout.readline()
            if output == '':
                break
            print(f"Debug: Sending to client {sid}: {output.strip()}")  # Debug print
            socketio.emit('output', {'data': output}, room=sid)
    finally:
        proc.stdout.close()
        proc.terminate()
        proc.wait()
        with lock:
            if sid in subprocesses:
                del subprocesses[sid]

@socketio.on('execute_script')
def handle_execute_script(json):
    script_name = json['script_name']
    sid = request.sid
    script_path = f'projects/{script_name}/main.py'  # Ensure this path is correct
    print(f"Attempting to start script at: {script_path}")  # Debug print

    with lock:
        if sid in subprocesses:
            old_proc_info = subprocesses.pop(sid, None)
            if old_proc_info and old_proc_info['process']:
                old_proc_info['process'].terminate()

        try:
            proc = subprocess.Popen(['python', script_path], stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            subprocesses[sid] = {'process': proc}

            thread = threading.Thread(target=read_output, args=(proc, sid))
            thread.start()
            subprocesses[sid]['thread'] = thread
            print(f"Started subprocess for {script_name} at {script_path}")
        except Exception as e:
            print(f"Failed to start subprocess for {script_name} at {script_path}: {str(e)}")
            if sid in subprocesses:
                del subprocesses[sid]

@socketio.on('input')
def handle_input(json):
    sid = request.sid
    data = json['data']
    with lock:
        if sid in subprocesses and 'process' in subprocesses[sid]:
            proc = subprocesses[sid]['process']
            proc.stdin.write(data)
            proc.stdin.flush()
        else:
            print(f"No subprocess found for session: {sid}")

@socketio.on('disconnect')
def handle_disconnect():
    with lock:
        if request.sid in subprocesses:
            proc_info = subprocesses.pop(request.sid, None)
            if proc_info and proc_info['process']:
                proc_info['process'].terminate()

if __name__ == '__main__':
    socketio.run(app, debug=True)
