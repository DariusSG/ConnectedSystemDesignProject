from copy import copy
from threading import Lock, Thread

import socketio

import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM

sio = socketio.Client(logger=True, engineio_logger=True)
GPIO.setup("P8_10", GPIO.IN)
PWM.start("P8_19", 50)
thread: Thread | None = None
thread_lock = Lock()

Sensor_Status = False
Alarm_Status = False
BoardState = ["AlarmStatus"]


@sio.event
def connect():
    global thread
    print('Connection established.')
    with thread_lock:
        PWM.stop("P8_19")
        if thread is None:
            thread = sio.start_background_task(background_thread)
            thread.daemon = True


@sio.event
def disconnect():
    global thread
    print('Disconnected from server.')
    with thread_lock:
        if thread is not None:
            thread = None
            PWM.stop("P8_19")


@sio.event
def StateUpdate(RxData: dict):
    global Alarm_Status
    if True:
        for key in BoardState:
            update_group = RxData.get(key, None)
            if update_group is not None:
                if key == "AlarmStatus":
                    if update_group["action"] == "update":
                        with thread_lock:
                            Alarm_Status = update_group["value"]
                    else:
                        print("Unknown action")
                else:
                    continue



def background_thread():
    global Sensor_Status
    while True:
        try:
            with thread_lock:
                DoorDetectionStatus = True if GPIO.input("P8_10") == 1 else False
                print("State:", DoorDetectionStatus)
                if not (Sensor_Status and DoorDetectionStatus):
                    Sensor_Status = copy(DoorDetectionStatus)
                    sio.emit(
                        "SensorUpdate",
                        {
                            "Door_Sensor": {
                                "action": "update",
                                "value": Sensor_Status
                            }
                        }
                    )
        except:
            print('Unable to transmit data.')
            pass
        if Alarm_Status:
            PWM.start("P8_19", 50)
            PWM.set_frequency("P8_19", 1000)
            print("Alarm")
            sio.sleep(0.1)
            PWM.set_frequency("P8_19", 2000)
            sio.sleep(0.1)
            PWM.stop("P8_19")
        sio.sleep(0.3)


def start_server():
    while True:
        try:
            sio.connect('http://192.168.0.170:5000')
            break
        except KeyboardInterrupt:
            break
        except:
            print("Trying to connect to the server.")
            pass
    sio.wait()


if __name__ == '__main__':
    start_server()
