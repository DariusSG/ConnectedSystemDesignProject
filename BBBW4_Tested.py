#BBBW4 clip 1 Box 17
import socketio
import time
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC as ADC

sio = socketio.Client()
ADC.setup()

@sio.event
def connect():
    print('Connection established.')

@sio.event
def disconnect():
    print('Disconnected from server.')

while True:
    # Trying to test if it can connect to ip.
    try:
        sio.connect('http://192.168.7.1:5000')
        break
    except:
        print("Try to connect to the server.")
        pass
    
while True:
    try:
        DigitalValue = ADC.read("P9_38")
        if DigitalValue != 0:
            AnalogVoltage = (DigitalValue * 1.8) * (2200 / 1200)
            DistanceCM = 29.988 * pow(AnalogVoltage , -1.173)
            print("Distance(cm): %f" % DistanceCM)
            sio.emit('BBBW2Event', {'data': ADC.read("P9_38")})
            
        time.sleep(0.3)

            
    except:
        print('Unable to transmit data.')
        pass


