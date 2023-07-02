from threading import Lock, Event, Thread

from socketio import Server, WSGIApp

socketio = Server(async_mode='threading')

thread_lock = Lock()
SensorState, clients = {}, []


# SENSOR EVENT
@socketio.event
def BBB2_Rx(RxData: dict):
    global SensorState
    with thread_lock:
        SensorState[RxData["sensor"]] = RxData["value"]


@socketio.event
def BBB3_Rx(RxData: dict):
    global SensorState
    with thread_lock:
        SensorState[RxData["sensor"]] = RxData["value"]


@socketio.event
def BBB4_Rx(RxData: dict):
    global SensorState
    with thread_lock:
        SensorState[RxData["sensor"]] = RxData["value"]


# UI EVENT
@socketio.event
def BBB1_Rx(RxData: dict):
    global SensorState
    with thread_lock:
        pass


class ApplicationThread(Thread):
    def __init__(self):
        super(ApplicationThread, self).__init__()
        self.daemon = True

        self.stopSignal: Event = Event()

    def run(self):
        global SensorState
        while self.stopSignal.is_set():
            # Draw UI
            # Handle Code
            # Send Data to UI
            socketio.emit("UI_Tx", {
                "state": "",
                "value": ""
            })

    def stop(self):
        self.stopSignal.set()


thread: ApplicationThread


@socketio.event
def connect(sid, environ, auth):
    global thread
    print('Connection established.')
    with thread_lock:
        if thread is None:
            thread = ApplicationThread()
            thread.start()
        if sid not in clients:
            clients.append(sid)


@socketio.event
def disconnect(sid):
    global thread
    if sid in clients:
        clients.remove(sid)
    if len(clients) == 0:
        thread.stop()


if __name__ == '__main__':
    app = WSGIApp(socketio)
    import eventlet
    from eventlet.wsgi import server as eventlet_wsgi_server
    eventlet_wsgi_server(eventlet.listen(('192.168.12.1', 8000)), app)
