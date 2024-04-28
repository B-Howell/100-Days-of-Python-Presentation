from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import subprocess
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Store process references by session ID to properly manage multiple users
processes = {}

@app.route('/terminal/<script_name>')
def terminal(script_name):
    return render_template('terminal.html', script_name=script_name)

@socketio.on('start_script')
def handle_start_script(json):
    script_name = json['script_name']
    script_path = os.path.join('projects', script_name, 'main.py')
    sid = request.sid  # Unique session identifier

    # Terminate any existing process for this session
    if sid in processes:
        old_process = processes[sid]
        old_process.terminate()

    # Start a new subprocess for the script
    try:
        process = subprocess.Popen(
            ['python', script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        processes[sid] = process

        def read_script_output(process):
            while True:
                output = process.stdout.readline()
                if output:
                    socketio.emit('script_output', {'data': output}, room=sid)
                else:
                    break
            process.terminate()
            exit_code = process.wait()
            socketio.emit('script_ended', {'code': exit_code}, room=sid)

        socketio.start_background_task(read_script_output, process)
    except Exception as e:
        emit('script_output', {'data': str(e)}, room=sid)

@socketio.on('user_input')
def handle_user_input(json):
    data = json['data']
    sid = request.sid
    if sid in processes:
        process = processes[sid]
        process.stdin.write(data + '\n')
        process.stdin.flush()

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    if sid in processes:
        process = processes.pop(sid, None)
        if process:
            process.terminate()

if __name__ == '__main__':
    socketio.run(app, debug=True)
