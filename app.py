from threading import Lock

from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

thread = None
thread_lock = Lock()

Magnet_Status = True
Door_Status = True


@socketio.event
def SensorUpdate(RxData: dict):
    global Magnet_Status
    update_group = RxData["Door_Sensor"]
    if update_group["action"] == "update":
        with thread_lock:
            Magnet_Status = update_group["value"]
    else:
        print("Unknown action")


@socketio.event
def StateUpdate(RxData: dict):
    global Door_Status
    if RxData.get("User_Door", False):
        update_group = RxData["User_Door"]
        if update_group["action"] == "update":
            with thread_lock:
                Door_Status = update_group["value"]
        elif update_group["action"] == "get":
            socketio.emit("WebUIUpdate", {"User_Door": {
                "action": "update",
                "value": Door_Status
            }})
        else:
            print("Unknown action")
    elif RxData.get("AlarmStatus", False):
        update_group = RxData["AlarmStatus"]
        if update_group["action"] == "get":
            socketio.emit("WebUIUpdate", {"AlarmStatus": {
                "action": "update",
                "value": Door_Status != Magnet_Status
            }})
        else:
            print("Unknown action")


@socketio.event
def connect():
    global thread
    print('Connection established.')
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(application_thread)


def application_thread():
    global Door_Status
    while True:
        socketio.sleep(0.5)
        if Door_Status == Magnet_Status:
            socketio.emit("StateUpdate", {
                "AlarmStatus": {
                    "action": "update",
                    "value": False
                }
            })
        else:
            socketio.emit("StateUpdate", {
                "AlarmStatus": {
                    "action": "update",
                    "value": True
                }
            })


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='192.168.12.1')
