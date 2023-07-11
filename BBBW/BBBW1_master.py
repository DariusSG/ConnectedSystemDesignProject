import time
from typing import Optional
from threading import Lock, Event, Thread

from socketio import Server, WSGIApp
from flask import Flask

from BBBW1_utils import FixedArray, RawConfig, KeyInput, OLED

import board
import busio
import digitalio
import adafruit_ssd1306
from board import SCL, SDA

CONFIG_FILE = "./CSDP.conf"
DEFAULT_CONFIG = {
    "TiltDistance": 0,
    "Password": "0000"
}
rawconfig = RawConfig(CONFIG_FILE)
rawconfig.load_default(DEFAULT_CONFIG)

socketio = Server(logger=True, async_mode='threading')
app = Flask(__name__)
app.wsgi_app = WSGIApp(socketio, app.wsgi_app)
app.config['SECRET_KEY'] = 'secret!'

thread: Optional['ApplicationThread'] = None
oledThread: Optional['OLEDThread'] = None
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
        "sensor": ["infra"],
        "value": {
            "infra": int,
        }
    }
}
SensorState = {
    "reed1": False,
    "reed2": False,
    "force1": 0,
    "force2": 0,
    "pot": 0,
    "keypad": 0,
    "keylock": 0,
    "infra": 0
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
    3: {
        "Temp": 0,
        "Alarm": False,
        "DoorOpen": False,
        "Weight": FixedArray(100)
    },
    4: {
        "Temp": 35,
        "Alarm": False,
        "DoorOpen": False,
        "Weight": FixedArray(100)
    },
}
InternalAlarm = False
clients = []

keyInput = KeyInput()


def OLEDClickInit():
    Pin_DC = digitalio.DigitalInOut(board.P9_16)
    Pin_DC.direction = digitalio.Direction.OUTPUT
    Pin_DC.value = False
    Pin_RESET = digitalio.DigitalInOut(board.P9_23)
    Pin_RESET.direction = digitalio.Direction.OUTPUT
    Pin_RESET.value = True
    L_I2c = busio.I2C(SCL, SDA)
    return L_I2c


G_I2c = OLEDClickInit()
Display = adafruit_ssd1306.SSD1306_I2C(64, 32, None, i2c_bus=G_I2c, i2c_address=0x3C)
oledDriver = OLED(Display)


def vaildateRxData(board, RxData: dict):
    board_config = SensorConfig.get(board)
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
    vaildateRxData("BBB2", RxData)
    with thread_lock:
        if not InternalAlarm:
            SensorState[RxData["sensor"]] = RxData["value"]


@socketio.event
def BBB3_Rx(RxData: dict):
    global SensorState
    vaildateRxData("BBB3", RxData)
    with thread_lock:
        SensorState[RxData["sensor"]] = RxData["value"]


@socketio.event
def BBB4_Rx(RxData: dict):
    global SensorState
    vaildateRxData("BBB4", RxData)
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
        InternalAlarm = False
        if TiltDistance < SensorState["infra"]:
            InternalAlarm = True
        for Compartment in CompartmentState.keys():
            if SensorState.get(f'reed{Compartment}') != CompartmentState[Compartment]['DoorOpen']:
                CompartmentState[Compartment]['Alarm'] = True
                InternalAlarm = True
            if (sum(CompartmentState[Compartment]['Weight'].getSlice(0,25))/25) < (sum(CompartmentState[Compartment]['Weight'].getSlice(25,50))/25):
                CompartmentState[Compartment]['Alarm'] = True
                InternalAlarm = True
            CompartmentState[Compartment]['Alarm'] = False


class OLEDThread(Thread):
    def __init__(self):
        super(OLEDThread, self).__init__()
        self.stopSignal: Event = Event()

    def run(self):
        global InternalAlarm, keyInput, oledDriver
        currentState, alarm_cycle, oled_pass = 'StandBy', [], ''
        retry_count, flagDisplay, Timeout = 0, False, None
        while not self.stopSignal.is_set():
            with thread_lock:
                keyInput.write_input('value')
                if currentState == 'StandBy':
                    oledDriver.TemperatureCycle()
                    keyInput.waiting = True
                    key = keyInput.getInput()
                    if key is not None:
                        oled_pass, retry_count, currentState = '', 0, 'Admin'
                elif currentState == 'Alarm':
                    if len(alarm_cycle) == 0:
                        alarm_cycle.append('blink')
                        for Compartment in CompartmentState.keys():
                            if CompartmentState[Compartment]['Alarm']:
                                alarm_cycle.extend([Compartment, 'blink'])
                    current_display = alarm_cycle.pop(0)
                    if isinstance(current_display, int):
                        oledDriver.ShowImage(f"./static/box_{current_display}.png")
                    else:
                        oledDriver.AlarmDisplay()
                    keyInput.waiting = True
                    key = keyInput.getInput()
                    if key is not None:
                        oled_pass, retry_count, currentState = '', 0, 'Admin'
                elif currentState == 'Admin':
                    if retry_count == 5:
                        currentState, retry_count = 'Alarm', 0
                    else:
                        if len(oled_pass) == 4:
                            if flagDisplay:
                                oledDriver.PassDisplay(oled_pass)
                            else:
                                flagDisplay = False
                                if oled_pass == rawconfig.getValue('USER', 'Password'):
                                    currentState, oled_pass, Timeout = "TempSet", '', time.thread_time()
                                    InternalAlarm = False
                                    for Compartment in CompartmentState.keys():
                                        CompartmentState[Compartment]['Alarm'] = False
                                    oledDriver.AGDisplay(True)
                                else:
                                    retry_count += 1
                                    oledDriver.AGDisplay(False)
                        else:
                            oledDriver.PassDisplay(oled_pass)
                            keyInput.waiting = True
                            key = keyInput.getInput()
                            if key is None:
                                continue
                            oled_pass += key[1]
                            flagDisplay = True if len(oled_pass) == 4 else False
                elif currentState == 'TempSet':
                    currentCompartment: int = SensorState['keylock'] + 1
                    TempSet: int = int((85 * SensorState['pot']) - 25)
                    oledDriver.TempDisplay(currentCompartment, TempSet)
                    CompartmentState[currentCompartment]['Temp'] = TempSet
                    if (time.thread_time() - Timeout) > 25:
                        currentState, Timeout = "StandBy", None
                    else:
                        Timeout = time.thread_time()
                if currentState == 'StandBy' and InternalAlarm:
                    currentState = 'Alarm'
                oledDriver.ShowDisplay()
            socketio.sleep(0.125)

    def stop(self):
        self.stopSignal.set()


class ApplicationThread(Thread):
    def __init__(self):
        super(ApplicationThread, self).__init__()
        self.stopSignal: Event = Event()

    def run(self):
        global SensorState, CompartmentState, InternalAlarm
        while not self.stopSignal.is_set():
            CheckAlarmStatus()
            socketio.emit("UI_Tx", {
                "state": "",
                "value": ""
            })
            socketio.sleep(0.25)

    def stop(self):
        self.stopSignal.set()


def ensureClients():
    ensure_list = ["BBB2","BBB3", "BBB4"]
    with thread_lock:
        for sid, sensor_node in clients:
            if sensor_node in ensure_list:
                ensure_list.remove(sensor_node)
            else:
                return False
    return True


@socketio.event
def connect(sid, environ, auth):
    global thread, oledThread
    print('Connection established.')
    with thread_lock:
        if sid not in clients:
            clients.append((sid, environ['SENSOR_NODE']))
        if thread is None and oledThread is None and ensureClients():
            thread = ApplicationThread()
            oledThread = OLEDThread()
            thread.start()
            oledThread.start()


@socketio.event
def disconnect(sid):
    global thread, oledThread
    if sid in clients:
        clients.remove(sid)
    if not ensureClients and thread is not None and oledThread is not None:
        thread.stop()
        oledThread.stop()
        thread, oledThread = None, None


if __name__ == '__main__':
    app.run(host='192.168.12.220',threaded=True)