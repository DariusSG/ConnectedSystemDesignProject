from threading import Lock

from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

thread = None
thread_lock = Lock()

SensorState = {}


# SENSOR EVENT
@socketio.event
def BBB2_Rx(RxData: dict):
    with thread_lock:
        SensorState[RxData["sensor"]] = RxData["value"]


@socketio.event
def BBB3_Rx(RxData: dict):
    with thread_lock:
        SensorState[RxData["sensor"]] = RxData["value"]


@socketio.event
def BBB4_Rx(RxData: dict):
    with thread_lock:
        SensorState[RxData["sensor"]] = RxData["value"]


# UI EVENT
@socketio.event
def BBB1_Rx(RxData: dict):
    pass



@socketio.event
def connect():
    global thread
    print('Connection established.')
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(application_thread)


def application_thread():
    # Draw UI
    # Handle Code
    # Send Data to UI
    socketio.emit('UI_Tx', {
        'state': "",
        'value': ""
    })


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='192.168.12.1')
