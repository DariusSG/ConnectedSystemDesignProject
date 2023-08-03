import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from threading import Lock, Thread

import socketio

from BBBW1_utils import OLED, SSD1306OLED

import board
import busio
import digitalio
from board import SCL, SDA
import Adafruit_BBIO.ADC as ADC
import Adafruit_BBIO.PWM as PWM

SERVER_IP = "http://192.168.12.1:5000"
SENSOR_NODE = "BBB1"
REFRESH = 0.2

sio = socketio.Client(logger=True, engineio_logger=True)

# GPIO SETUP
ADC.setup()
PWM.start("P8_19", 50)
PWM.stop("P8_19")

Pin_DC = digitalio.DigitalInOut(board.P9_16)
Pin_DC.direction = digitalio.Direction.OUTPUT
Pin_DC.value = False

i2c = busio.I2C(SCL, SDA)
while not i2c.try_lock():
    pass

reset = digitalio.DigitalInOut(board.P9_23)
reset.direction = digitalio.Direction.OUTPUT

oledDriver = OLED(SSD1306OLED(reset, i2c, 0x3C, 96, 40))

# EOF
thread: Optional[Thread] = None
thread_lock = Lock()

Alarm = False
OLEDSTATE = {
    "state": "",
    "value": ()
}


@sio.event
def BBB1_Rx(RxData: dict):
    global Alarm, OLEDSTATE
    if RxData['act'] == 'update':
        if RxData['value']['object'] == 'alarm':
            Alarm = RxData['value']['value']
        elif RxData['value']['object'] == 'oled':
            OLEDSTATE = RxData['value']['value']
        return 200


@sio.event
def connect():
    print('Connection established.')


@sio.event
def disconnect():
    print('Disconnected from server.')


def background_thread():
    while True:
        try:
            with thread_lock:
                # GET SENSOR DATA
                payload: list = [{
                    'sensor': 'keypad',
                    'value': ADC.read("P9_38")
                }]

                sio.emit(f'{SENSOR_NODE}_Rx', {
                    'sensor': 'all',
                    'value': payload
                })
        except Exception as e:
            print('Unable to transmit data.')
            print(e)
            pass
        time.sleep(REFRESH)


def alarm_thread():
    global Alarm
    while True:
        if Alarm:
            print("Alarm")
            PWM.start("P8_19", 50)
            PWM.set_frequency("P8_19", 1000)
            time.sleep(0.1)
            PWM.set_frequency("P8_19", 2000)
            time.sleep(0.1)
            PWM.stop("P8_19")
        time.sleep(0.1)


def oled_thread():
    global OLEDSTATE, oledDriver
    while True:
        state = OLEDSTATE.get("state", None)
        val: tuple | str | list | bool | None = OLEDSTATE.get("value", None)
        print(state, val)
        if state == 'OLED_Display':
            oledDriver.OLED_Display(*val)

        elif state == 'TemperatureCycle':
            oledDriver.TemperatureCycle(val)

        elif state == 'ShowImage':
            oledDriver.ShowImage(val)

        elif state == 'AlarmDisplay':
            oledDriver.AlarmDisplay()

        elif state == 'AGDisplay':
            oledDriver.AGDisplay(val)

        elif state == 'PassDisplay':
            oledDriver.PassDisplay(val)

        elif state == 'TempSetDisplay':
            oledDriver.TempSetDisplay(*val)
        oledDriver.ShowDisplay()
        sio.sleep(0.25)


if __name__ == '__main__':
    while True:
        try:
            sio.connect(SERVER_IP)
            break
        except KeyboardInterrupt:
            break
        except Exception:
            print("Trying to connect to the server.")
            pass
    sio.sleep(1)
    sio.start_background_task(oled_thread)
    sio.start_background_task(alarm_thread)
    sio.start_background_task(background_thread)