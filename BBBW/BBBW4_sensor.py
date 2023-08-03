import time
from threading import Lock, Thread
from typing import Optional

import socketio

import Adafruit_BBIO.ADC as ADC

SERVER_IP = "http://192.168.12.1:5000"
SENSOR_NODE = "BBB4"
REFRESH = 2

sio = socketio.Client(logger=True, engineio_logger=True)

# GPIO SETUP
ADC.setup()
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
                
                # BBBW4 Clip 1
                sio.emit(f'{SENSOR_NODE}_Rx', {
                    'sensor': 'infra',
                    'value': ADC.read("P9_38")
                })
            
        except:
            print('Unable to transmit data.')
            pass
        sio.sleep(REFRESH)


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
    sio.sleep(1)
    background_thread()
