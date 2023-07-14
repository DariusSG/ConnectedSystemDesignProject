import time
from typing import Optional
from threading import Lock, Thread

import socketio

import Adafruit_BBIO.ADC as ADC
import Adafruit_BBIO.GPIO as GPIO

SERVER_IP = "http://192.168.12.2:5000"
SENSOR_NODE = "BBB2"
REFRESH = 0.5

sio = socketio.Client(logger=True, engineio_logger=True)

# GPIO SETUP
ADC.setup()
GPIO.setup("P8_10", GPIO.IN)
GPIO.setup("P9_42", GPIO.IN)

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
                sio.emit(f'{SENSOR_NODE}_Rx', {
                    'sensor': 'reed1',
                    'value': GPIO.input("P8_10")
                })

                sio.emit(f'{SENSOR_NODE}_Rx', {
                    'sensor': 'reed2',
                    'value': GPIO.input("P9_42")
                })
                
                sio.emit(f'{SENSOR_NODE}_Rx', {
                    'sensor': 'force1',
                    'value': ADC.read("P9_38")
                })

                sio.emit(f'{SENSOR_NODE}_Rx', {
                    'sensor': 'force2',
                    'value': ADC.read("P9_40")
                })
        
        except Exception as e:
            print('Unable to transmit data.')
            print(e)
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
