from typing import Optional
from threading import Lock, Event, Thread

from flask_socketio import SocketIO
from flask import Flask

from BBBW1_utils import FixedArray, RawConfig, KeyInput, OLED, SSD1306OLED

import board
import busio
import digitalio
from board import SCL, SDA
import Adafruit_BBIO.ADC as ADC
import Adafruit_BBIO.PWM as PWM

CONFIG_FILE = "./CSDP.conf"
DEFAULT_CONFIG = {
    "TiltDistance": 0,
    "Password": "1111"
}
rawconfig = RawConfig(CONFIG_FILE)
rawconfig.load_default(DEFAULT_CONFIG)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

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
        "Weight": FixedArray(20)
    },
    2: {
        "Temp": 0,
        "Alarm": False,
        "DoorOpen": False,
        "Weight": FixedArray(20)
    },
    3: {
        "Temp": 0,
        "Alarm": False,
        "DoorOpen": False,
        "Weight": FixedArray(20)
    },
    4: {
        "Temp": 35,
        "Alarm": False,
        "DoorOpen": False,
        "Weight": FixedArray(20)
    },
}
Timeout = 10
InternalAlarm = False
ResetStatus = False
clients = []

ADC.setup()
PWM.start("P8_19", 50)
PWM.stop("P8_19")
keyInput = KeyInput()

Pin_DC = digitalio.DigitalInOut(board.P9_16)
Pin_DC.direction = digitalio.Direction.OUTPUT
Pin_DC.value = False

i2c = busio.I2C(SCL, SDA)
while not i2c.try_lock():
    pass

reset = digitalio.DigitalInOut(board.P9_23)
reset.direction = digitalio.Direction.OUTPUT

oledDriver = OLED(SSD1306OLED(reset, i2c, 0x3C, 96, 40))


def vaildateRxData(board, RxData: dict):
    board_config = SensorConfig.get(board)
    if RxData["sensor"] not in board_config["sensor"]:
        app.logger.warning(f'Unknown Sensor {RxData["sensor"]} sent from BBB2')
        return False
    if isinstance(board_config["value"][RxData["sensor"]], list):
        if RxData["value"] not in board_config["value"][RxData["sensor"]]:
            app.logger.warning(f'Unknown Value from Sensor {RxData["sensor"]} sent from BBB2')
            return False
    elif isinstance(board_config["value"][RxData["sensor"]], type):
        if isinstance(RxData["value"], board_config["value"][RxData["sensor"]]):
            app.logger.warning(f'Unknown Value from Sensor {RxData["sensor"]} sent from BBB2')
            return False
    return True


# SENSOR EVENT
@socketio.event
def BBB2_Rx(RxData: dict):
    global SensorState
    with thread_lock:
        if RxData["sensor"] == 'all':
            for data in RxData['value']:
                vaildateRxData("BBB2", data)
                SensorState[data["sensor"]] = data["value"]


@socketio.event
def BBB3_Rx(RxData: dict):
    global SensorState
    with thread_lock:
        if RxData["sensor"] == 'all':
            for data in RxData['value']:
                vaildateRxData("BBB3", data)
                SensorState[data["sensor"]] = data["value"]


@socketio.event
def BBB4_Rx(RxData: dict):
    global SensorState
    vaildateRxData("BBB4", RxData)
    with thread_lock:
        SensorState[RxData["sensor"]] = RxData["value"]


# UI EVENT
@socketio.event
def BBB1_Rx(RxData: dict):
    global rawconfig, CompartmentState, ResetStatus, Timeout
    with thread_lock:
        if RxData['act'] == 'get':
            if RxData['key'] == 'state':
                boxID = RxData['value']
                weight = sum(CompartmentState[boxID]['Weight'].getSlice(0, 5)) / 5
                print("UI_Tx", {
                    "act": 'update',
                    "key": 'state',
                    'value': {
                        'boxID': boxID,
                        'Temp': CompartmentState[boxID]['Temp'],
                        'DoorOpen': CompartmentState[boxID]['DoorOpen'],
                        'Weight': weight
                    }
                })
                socketio.emit("UI_Tx", {
                    "act": 'update',
                    "key": 'state',
                    'value': {
                        'boxID': boxID,
                        'Temp': CompartmentState[boxID]['Temp'],
                        'DoorOpen': CompartmentState[boxID]['DoorOpen'],
                        'Weight': weight
                    }
                })
            elif RxData['key'] == 'alarm_pin':
                if RxData['value']['prev'] == rawconfig.getValue("USER", "Password"):
                    socketio.emit("UI_Tx", {
                        "act": 'update',
                        "key": 'alarm_RESET'
                    })
                    ResetStatus = True
                else:
                    return 400
            else:
                return 415
        elif RxData['act'] == 'update':
            if RxData['key'] == 'password':
                if RxData['value'] == rawconfig.getValue("USER", "Password"):
                    rawconfig.writeValue("USER", "Password", RxData['value']['new'])
                else:
                    return 400
            elif RxData['key'] == 'state':
                boxID = RxData['value']['BoxID']
                CompartmentState[boxID]['Temp'] = RxData['value']['Temp']
                CompartmentState[boxID]['DoorOpen'] = RxData['value']['DoorOpen']
            elif RxData['key'] == 'timeout':
                if RxData['value']['pin'] == rawconfig.getValue("USER", "Password"):
                    Timeout = RxData['value']['timeout']
                else:
                    return 400
        else:
            return 501
        return 200


def CheckAlarmStatus():
    global CompartmentState, InternalAlarm
    with thread_lock:
        try:
            TiltDistance = int(rawconfig.getValue("USER", "TiltDistance"))
            InternalAlarm = False
            if 10 < int(TiltDistance - SensorState["infra"]) < 10:
                print("Alarm Active From Infra")
                # InternalAlarm = True
            for Compartment in CompartmentState.keys():
                CompartmentState[Compartment]['Alarm'] = False
                if Compartment in [3, 4]:
                    continue
                if (not CompartmentState[Compartment]['DoorOpen']) and SensorState.get(f'reed{Compartment}') != \
                        CompartmentState[Compartment]['DoorOpen']:
                    CompartmentState[Compartment]['Alarm'] = True
                    InternalAlarm = True
                    print(f"Alarm Active From Reed {Compartment}")
                new_val = round(1000 * (sum(CompartmentState[Compartment]['Weight'].getSlice(0, 5)) / 5), 5)
                prev_val = round(1000 * (sum(CompartmentState[Compartment]['Weight'].getSlice(5, 10)) / 5), 5)
                print(f'{Compartment}', prev_val, new_val)
                if (not CompartmentState[Compartment]['DoorOpen']) and ((prev_val - new_val) > 400):
                    CompartmentState[Compartment]['Alarm'] = True
                    InternalAlarm = True
                    print(f"Alarm Active From Force {Compartment}")

            if InternalAlarm:
                socketio.emit("UI_Rx", {
                    "act": "update",
                    "key": "alarm"
                })
        except:
            pass


def Recalibrate():
    global InternalAlarm, ResetStatus
    InternalAlarm = False
    rawconfig.writeValue("USER", "TiltDistance", str(SensorState['infra']))
    socketio.sleep(0.25)
    for Compartment in CompartmentState.keys():
        CompartmentState[Compartment]['Weight'] = FixedArray(100)
        socketio.sleep(0.25)
    ResetStatus = False


class OLEDThread(Thread):
    def __init__(self):
        super(OLEDThread, self).__init__()
        self.stopSignal: Event = Event()
        self.currentState = 'StandBy'
        self.alarm_cycle = []
        self.oled_pass = ''
        self.retry_count = 0
        self.flagDisplay = False

    def runState(self):
        global InternalAlarm, keyInput, oledDriver, ResetStatus
        if ResetStatus:
            oledDriver.OLED_Display(['Reset In', 'Progress'])
        elif self.currentState == 'StandBy':
            # currentCompartment: int = SensorState['keylock'] + 1
            # oledDriver.TempDisplay(currentCompartment, CompartmentState[currentCompartment]['Temp'])
            oledDriver.TemperatureCycle(
                [CompartmentState[Compartment]['Temp'] for Compartment in CompartmentState.keys()])
            if keyInput.getInput() is not None:
                self.oled_pass, self.retry_count, self.currentState = '', 0, 'Admin'
                return
        elif self.currentState == 'Alarm':
            if len(self.alarm_cycle) == 0:
                self.alarm_cycle.append('blink')
                for Compartment in CompartmentState.keys():
                    if CompartmentState[Compartment]['Alarm']:
                        self.alarm_cycle.extend([Compartment, 'blink'])
            current_display = self.alarm_cycle.pop(0)
            if isinstance(current_display, int):
                oledDriver.ShowImage(f"./static/box_{current_display}.png")
            else:
                oledDriver.AlarmDisplay()
            if keyInput.getInput() is not None:
                self.oled_pass, self.retry_count, self.currentState = '', 0, 'Admin'
        elif self.currentState == 'Admin':
            if self.retry_count == 5:
                self.currentState, self.retry_count = 'Timeout', 0
            else:
                if len(self.oled_pass) == 4:
                    if self.flagDisplay:
                        oledDriver.PassDisplay(self.oled_pass)
                        self.flagDisplay = False
                    else:
                        if self.oled_pass == rawconfig.getValue('USER', 'Password'):
                            self.currentState, self.oled_pass = "TempSet", ''
                            if InternalAlarm:
                                ResetStatus = True
                            for Compartment in CompartmentState.keys():
                                CompartmentState[Compartment]['Alarm'] = False
                            socketio.sleep(0.5)
                            oledDriver.AGDisplay(True)
                        else:
                            self.retry_count += 1
                            self.oled_pass = ''
                            oledDriver.AGDisplay(False)
                else:
                    oledDriver.PassDisplay(self.oled_pass)
                    key = keyInput.getKeyPress()
                    if key is not None:
                        self.oled_pass += key[1]
                        self.flagDisplay = True if len(self.oled_pass) == 4 else False
        elif self.currentState == 'TempSet':
            currentCompartment: int = SensorState['keylock'] + 1
            TempSet: int = int((85 * SensorState['pot']) - 25)
            oledDriver.TempSetDisplay(currentCompartment, TempSet)
            CompartmentState[currentCompartment]['Temp'] = TempSet
            if keyInput.getInput() is not None:
                self.currentState = "StandBy"
        elif self.currentState == 'Timeout':
            oledDriver.OLED_Display(['Timeout'], coords=(2, 1))
            oledDriver.ShowDisplay()
            socketio.sleep(Timeout)
            self.currentState = 'Admin'
        if self.currentState == 'StandBy' and InternalAlarm:
            self.currentState = 'Alarm'
        elif self.currentState in ['TempSet'] and InternalAlarm:
            ResetStatus = True

    def run(self):
        while not self.stopSignal.is_set():
            print(self.currentState, self.alarm_cycle, self.oled_pass, self.retry_count, self.flagDisplay)
            with thread_lock:
                keyInput.write_input(ADC.read("P9_38"))
                self.runState()
                oledDriver.ShowDisplay()
            socketio.sleep(0.25)

    def stop(self):
        self.stopSignal.set()


class ApplicationThread(Thread):
    def __init__(self):
        super(ApplicationThread, self).__init__()
        self.stopSignal: Event = Event()

    def run(self):
        global SensorState, CompartmentState, InternalAlarm
        Recalibrate()
        socketio.sleep(1)
        while not self.stopSignal.is_set():
            for boxID in CompartmentState.keys():
                if boxID in [3, 4]:
                    continue
                CompartmentState[boxID]['Weight'].add(SensorState[f'force{boxID}'])
            if ResetStatus:
                Recalibrate()
            elif not InternalAlarm:
                CheckAlarmStatus()
            if InternalAlarm:
                PWM.start("P8_19", 50)
                PWM.set_frequency("P8_19", 1000)
                print("Alarm")
                socketio.sleep(0.1)
                PWM.set_frequency("P8_19", 2000)
                socketio.sleep(0.1)
                PWM.stop("P8_19")
            socketio.sleep(0.25)

    def stop(self):
        self.stopSignal.set()


@socketio.on('connect')
def connect():
    global thread, oledThread
    print('Connection established')
    with thread_lock:
        if thread is None and oledThread is None:
            thread = ApplicationThread()
            oledThread = OLEDThread()
            thread.start()
            oledThread.start()


@socketio.on('disconnect')
def disconnect():
    global thread, oledThread
    print('Disconnected from server.')


if __name__ == '__main__':
    socketio.run(app, host='192.168.12.2')
