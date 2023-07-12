from threading import Lock, Thread

import socketio

import Adafruit_BBIO.ADC as ADC

import Adafruit_BBIO.GPIO as GPIO

SERVER_IP = "http://192.168.12.2:5000"
SENSOR_NODE = "BBB3"
REFRESH = 2

sio = socketio.Client(logger=True, engineio_logger=True)

# GPIO SETUP
ADC.setup()
GPIO.setup("P9_12", GPIO.IN)
GPIO.setup("P9_14", GPIO.IN)
GPIO.setup("P9_15", GPIO.IN)


# EOF
thread: Thread | None = None
thread_lock = Lock()


@sio.event
def connect():
    global thread
    print('Connection established.')
    with thread_lock:
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

                sio.emit(f'{SENSOR_NODE}_Rx', {
                    'sensor': 'keylock',
                    'value': keylock
                })

                sio.emit(f'{SENSOR_NODE}_Rx', {
                    'sensor': 'pot',
                    'value': ADC.read("P9_37")
                })
        
        except:
            print('Unable to transmit data.')
            pass
        sio.sleep(REFRESH)


def start_server():
    while True:
        try:
            sio.connect(SERVER_IP, headers={"SENSOR_NODE": SENSOR_NODE})
            break
        except KeyboardInterrupt:
            break
        except:
            print("Trying to connect to the server.")
            pass
    sio.wait()


if __name__ == '__main__':
    start_server()
