import time
from threading import Lock, Event, Thread

import app
from ClientUI import socketio
from ClientUI.sensorConfig import vaildateRxData
from ClientUI.utils import RawConfig, FixedArray, KeyInput

CONFIG_FILE = "./CSDP.conf"
DEFAULT_CONFIG = {
    "TiltDistance": 0,
    "Password": "1111"
}

rawconfig = RawConfig(CONFIG_FILE)
rawconfig.load_default(DEFAULT_CONFIG)
print("Password: ", rawconfig.getValue('USER', "Password"))

thread_lock = Lock()

keyInput = KeyInput()

Timeout = 10
InternalAlarm = False
ResetStatus = False
HoldAlarm = False
OLEDWait = False

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
        "Weight": FixedArray(5)
    },
    2: {
        "Temp": 0,
        "Alarm": False,
        "DoorOpen": False,
        "Weight": FixedArray(5)
    },
    3: {
        "Temp": 0,
        "Alarm": False,
        "DoorOpen": False,
        "Weight": FixedArray(5)
    },
    4: {
        "Temp": 35,
        "Alarm": False,
        "DoorOpen": False,
        "Weight": FixedArray(5)
    },
}


@socketio.event
def BBB1_Rx(RxData: dict):
    global SensorState
    with thread_lock:
        if RxData["sensor"] == 'all':
            for data in RxData['value']:
                vaildateRxData("BBB1", data)
                SensorState[data["sensor"]] = data["value"]


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
def UI_Rx(RxData: dict):
    global rawconfig, CompartmentState, ResetStatus, Timeout
    with thread_lock:
        if RxData['act'] == 'get':
            if RxData['key'] == 'state':
                boxID = RxData['value']
                weight = 1000 * (
                        sum(CompartmentState[boxID]['Weight'].getSlice(0, 2)) / 2)
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
                if InternalAlarm:
                    socketio.emit("UI_Tx", {
                        "act": 'update',
                        "key": 'alarm'
                    })
            elif RxData['key'] == 'alarm_pin':
                if RxData['value'] == rawconfig.getValue("USER", "Password"):
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
                if RxData['value']['prev'] == rawconfig.getValue("USER", "Password"):
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
        TiltDistance = 100 * float(rawconfig.getValue("USER", "TiltDistance"))
        InternalAlarm = False
        print("Tilt", TiltDistance, 100 * SensorState["infra"])
        if not (-5 < int(TiltDistance - (100 * SensorState["infra"])) < 5):
            print("Alarm Active From Infra")
            InternalAlarm = True
        for Compartment in CompartmentState.keys():
            CompartmentState[Compartment]['Alarm'] = False
            if Compartment in [3, 4]:
                continue
            if (not CompartmentState[Compartment]['DoorOpen']) \
                    and (not SensorState.get(f'reed{Compartment}')) != \
                    CompartmentState[Compartment]['DoorOpen']:
                CompartmentState[Compartment]['Alarm'] = True
                InternalAlarm = True
                print(f"Alarm Active From Reed {Compartment}")
            new_val = round(1000 * (
                    sum(CompartmentState[Compartment]['Weight'].getSlice(0, 2)) / 2), 5)
            prev_val = round(1000 * (
                    sum(CompartmentState[Compartment]['Weight'].getSlice(2, 4)) / 2), 5)
            print(Compartment, new_val, prev_val)
            if (not CompartmentState[Compartment]['DoorOpen']) \
                    and ((new_val - prev_val) > 250):
                CompartmentState[Compartment]['Alarm'] = True
                InternalAlarm = True
                print(f"Alarm Active From Force {Compartment}")


def Recalibrate():
    global InternalAlarm, ResetStatus
    InternalAlarm = False
    rawconfig.writeValue("USER", "TiltDistance", str(SensorState['infra']))
    socketio.sleep(0.25)
    for Compartment in CompartmentState.keys():
        CompartmentState[Compartment]['Weight'] = FixedArray(5)
        socketio.sleep(0.25)
    ResetStatus = False


def ackCommandOLED(result):
    global OLEDWait
    if OLEDWait:
        if result == 200:
            print("OLED command Successful")
        else:
            print("OLED Command Failure")
        OLEDWait = False


def sendCommandOLED(state, args):
    global OLEDWait
    socketio.emit("BBB1_Rx", {
            "act": "update",
            "value": {
                "object": "oled",
                "value": {
                    "state": state,
                    "value": args
                }
            }
    })


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
        global InternalAlarm, keyInput, ResetStatus, HoldAlarm
        if ResetStatus:
            # sendCommandOLED("OLED_Display", (['Reset In', 'Progress']))
            self.currentState = 'StandBy'
        elif self.currentState == 'StandBy':
            sendCommandOLED("TemperatureCycle",
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
                sendCommandOLED("ShowImage", f"./static/box_{current_display}.png")
            else:
                sendCommandOLED("AlarmDisplay", ())
            if keyInput.getInput() is not None:
                self.oled_pass, self.retry_count, self.currentState = '', 0, 'Admin'
        elif self.currentState == 'Admin':
            if self.retry_count == 5:
                self.currentState, self.retry_count = 'Timeout', 0
            else:
                if len(self.oled_pass) == 4:
                    if self.flagDisplay:
                        sendCommandOLED("PassDisplay", self.oled_pass)
                        self.flagDisplay = False
                    else:
                        if self.oled_pass == rawconfig.getValue('USER', 'Password'):
                            self.currentState, self.oled_pass = "TempSet", ''
                            if InternalAlarm:
                                ResetStatus = True
                            for Compartment in CompartmentState.keys():
                                CompartmentState[Compartment]['Alarm'] = False
                            socketio.sleep(0.5)
                            sendCommandOLED("AGDisplay", True)
                        else:
                            self.retry_count += 1
                            self.oled_pass = ''
                            sendCommandOLED("AGDisplay", False)
                else:
                    sendCommandOLED("PassDisplay", self.oled_pass)
                    key = keyInput.getKeyPress()
                    if key is not None:
                        self.oled_pass += key[1]
                        self.flagDisplay = True if len(self.oled_pass) == 4 else False
        elif self.currentState == 'TempSet':
            HoldAlarm = True
            for comp in CompartmentState:
                CompartmentState[comp]["DoorOpen"] = True
            currentCompartment: int = SensorState['keylock'] + 1
            TempSet: int = int((85 * SensorState['pot']) - 25)
            sendCommandOLED("TempSetDisplay", (currentCompartment, TempSet))
            CompartmentState[currentCompartment]['Temp'] = TempSet
            if keyInput.getInput() is not None:
                self.currentState = "StandBy"
                for comp in CompartmentState:
                    CompartmentState[comp]["DoorOpen"] = False
                ResetStatus, HoldAlarm = True, False
        elif self.currentState == 'Timeout':
            # sendCommandOLED("OLED_Display", (['Timeout'], {"coords": (2, 1)}))
            socketio.sleep(Timeout + 5)
            self.currentState = 'Admin'
        if self.currentState == 'StandBy' and InternalAlarm:
            self.currentState = 'Alarm'

    def run(self):
        global OLEDWait
        while True:
            print("OLED Heartbeat")
            self.runState()
            socketio.sleep(0.35)

    def stop(self):
        self.stopSignal.set()


class ApplicationThread(Thread):
    def __init__(self):
        super(ApplicationThread, self).__init__()
        self.stopSignal: Event = Event()

    def run(self):
        global SensorState, CompartmentState, InternalAlarm, keyInput
        Recalibrate()
        socketio.sleep(1)
        while True:
            print("Heartbeat")
            try:
                keyInput.write_input(SensorState.get("keypad"))
                CompartmentState[1]['Weight'].add(SensorState[f'force{1}'])
                CompartmentState[2]['Weight'].add(SensorState[f'force{2}'])
                if ResetStatus:
                    Recalibrate()
                elif (not InternalAlarm) and (not HoldAlarm):
                    CheckAlarmStatus()
                if InternalAlarm:
                    socketio.emit("BBB1_Rx", {
                        'act': "update",
                        'value': {
                            'object': 'alarm',
                            'value': InternalAlarm
                        }
                    })
            except Exception as e:
                print(e)
            socketio.sleep(0.5)

    def stop(self):
        self.stopSignal.set()


@socketio.on('connect')
def connect():
    global thread, oledThread
    print('Connection established')


@socketio.on('disconnect')
def disconnect():
    global thread, oledThread
    print('Disconnected from server.')


thread = ApplicationThread()
oledThread = OLEDThread()
thread.start()
oledThread.start()