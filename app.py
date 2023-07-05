from threading import Lock, Event, Thread

from socketio import Server, WSGIApp

from app_utils import FixedArray, RawConfig

CONFIG_FILE = "./CSDP.conf"
DEFAULT_CONFIG = {
    "TiltDistance": 0,
    "Password": "0000"
}
rawconfig = RawConfig(CONFIG_FILE)
rawconfig.load_default(DEFAULT_CONFIG)

socketio = Server(async_mode='threading')

thread_lock = Lock()
SensorConfig = {
    "BBB2": {
        "sensor": ["reed1", "reed2", "force1", "force2"],
        "value": {
            "reed1": bool,
            "reed2": bool,
            "force1": int,
            "force2": int
        }
    },
    "BBB3": {
        "sensor": ["pot", "keylock"],
        "value": {
            "pot": int,
            "keylock": [0, 1, 2],
        }
    },
    "BBB4": {
        "sensor": ["keypad", "infra"],
        "value": {
            "keypad": [f'T{i}' for i in range(1, 7)],
            "infra": int,
        }
    }
}
SensorState = {
    "reed1": None,
    "reed2": None,
    "force1": None,
    "force2": None,
    "pot": None,
    "keypad": None,
    "keylock": None,
    "infra": None
}
CompartmentState = {
    1: {
        "Temp": 0,
        "Alarm": False,
        "DoorOpen": False,
        "Weight": FixedArray(100)
    },
    2: {
        "Temp": 0,
        "Alarm": False,
        "DoorOpen": False,
        "Weight": FixedArray(100)
    },
}
InternalAlarm = False
clients = []


def vaildateRxData(RxData: dict):
    board_config = SensorConfig.get("BBB2")
    if RxData["sensor"] not in board_config["sensor"]:
        socketio.logger.warning(f'Unknown Sensor {RxData["sensor"]} sent from BBB2')
        return False
    if isinstance(board_config["value"][RxData["sensor"]], list):
        if RxData["value"] not in board_config["value"][RxData["sensor"]]:
            socketio.logger.warning(f'Unknown Value from Sensor {RxData["sensor"]} sent from BBB2')
            return False
    elif isinstance(board_config["value"][RxData["sensor"]], type):
        if isinstance(RxData["value"], board_config["value"][RxData["sensor"]]):
            socketio.logger.warning(f'Unknown Value from Sensor {RxData["sensor"]} sent from BBB2')
            return False
    return True


# SENSOR EVENT
@socketio.event
def BBB2_Rx(RxData: dict):
    global SensorState
    vaildateRxData(RxData)
    with thread_lock:
        SensorState[RxData["sensor"]] = RxData["value"]


@socketio.event
def BBB3_Rx(RxData: dict):
    global SensorState
    vaildateRxData(RxData)
    with thread_lock:
        SensorState[RxData["sensor"]] = RxData["value"]


@socketio.event
def BBB4_Rx(RxData: dict):
    global SensorState
    vaildateRxData(RxData)
    with thread_lock:
        SensorState[RxData["sensor"]] = RxData["value"]


# UI EVENT
@socketio.event
def BBB1_Rx(RxData: dict):
    with thread_lock:
        if RxData['act'] == 'get':
            if RxData['sensor'] in SensorState.keys():
                socketio.emit("UI_Tx", {
                    "state": RxData['sensor'],
                    "value": SensorState[RxData['sensor']]
                })
                return 200
            else:
                return 415
        elif RxData['act'] == 'update':
            if RxData['key'] == 'Password':
                rawconfig.writeValue("USER", "Password", RxData['value'])
            pass  # TODO: add UI Related Values
        else:
            return 501


def CheckAlarmStatus():
    global CompartmentState, InternalAlarm
    with thread_lock:
        TiltDistance = rawconfig.getValue("USER", "TiltDistance")
        if TiltDistance < SensorState["infra"]:
            InternalAlarm = True
            return True
        InternalAlarm = False
        for Compartment in CompartmentState.keys():
            if SensorState.get(f'reed{Compartment}') != CompartmentState[Compartment]['DoorOpen']:
                CompartmentState[Compartment]['Alarm'] = True
                return True
            if (sum(CompartmentState[Compartment]['Weight'].getSlice(0,25))/25) < (sum(CompartmentState[Compartment]['Weight'].getSlice(25,50))/25):
                CompartmentState[Compartment]['Alarm'] = True
                return True
            CompartmentState[Compartment]['Alarm'] = False
    return False


class ApplicationThread(Thread):
    def __init__(self):
        super(ApplicationThread, self).__init__()
        self.daemon = True
        self.stopSignal: Event = Event()

    def run(self):
        global SensorState
        while self.stopSignal.is_set():
            CheckAlarmStatus()

            # Draw UI
            # Handle Code
            # Send Data to UI
            socketio.emit("UI_Tx", {
                "state": "",
                "value": ""
            })
            socketio.sleep(0.25)

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
