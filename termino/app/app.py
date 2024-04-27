from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import subprocess
import os
import shlex

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route('/terminal/<script_name>')
def terminal(script_name):
    return render_template('terminal.html', script_name=script_name)

@socketio.on('start_script')
def handle_start_script(json):
    script_name = json['script_name']
    script_path = os.path.join('projects', script_name, 'main.py')

    try:
        process = subprocess.Popen(['python', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True)

        def read_script_output():
            while True:
                output = process.stdout.readline()
                if output:
                    socketio.emit('script_output', {'data': output})
                else:
                    break
            process.stdout.close()
            exit_code = process.wait()
            socketio.emit('script_ended', {'code': exit_code})

        socketio.start_background_task(read_script_output)
    except Exception as e:
        emit('script_output', {'data': str(e)})

if __name__ == '__main__':
    socketio.run(app, debug=True)
