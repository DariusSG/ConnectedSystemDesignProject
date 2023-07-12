from threading import Lock, Thread

import socketio

import Adafruit_BBIO.ADC as ADC

SERVER_IP = "http://192.168.12.2:5000"
SENSOR_NODE = "BBB4"
REFRESH = 2

sio = socketio.Client(logger=True, engineio_logger=True)

# GPIO SETUP
ADC.setup()
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
                
                # BBBW4 Clip 1
                sio.emit(f'{SENSOR_NODE}_Rx', {
                    'sensor': 'infra',
                    'value': ADC.read("P9_38")
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
