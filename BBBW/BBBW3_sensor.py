import time
from threading import Lock, Thread
from typing import Optional

import socketio

import Adafruit_BBIO.ADC as ADC
import Adafruit_BBIO.GPIO as GPIO

SERVER_IP = "http://192.168.12.1:5000"
SENSOR_NODE = "BBB3"
REFRESH = 4

sio = socketio.Client(logger=True, engineio_logger=True)

# GPIO SETUP
ADC.setup()
GPIO.setup("P9_12", GPIO.IN)
GPIO.setup("P9_14", GPIO.IN)
GPIO.setup("P9_15", GPIO.IN)


# EOF
thread: Optional[Thread] = None
thread_lock = Lock()


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
                keylock = None
                if GPIO.input("P9_12"):
                    keylock = 0
                elif GPIO.input("P9_14"):
                    keylock = 1
                elif GPIO.input("P9_15"):
                    keylock = 2

                payload = [{
                    'sensor': 'keylock',
                    'value': keylock
                },{
                    'sensor': 'pot',
                    'value': round((round(ADC.read("P9_37"),3) / 0.628), 3)
                }]

                sio.emit(f'{SENSOR_NODE}_Rx', {
                    'sensor': 'all',
                    'value': payload
                })
        
        except:
            print('Unable to transmit data.')
            pass
        time.sleep(REFRESH)


if __name__ == '__main__':
    while True:
        try:
            sio.connect(SERVER_IP)
            break
        except KeyboardInterrupt:
            break
        except:
            print("Trying to connect to the server.")
            pass
    background_thread()
