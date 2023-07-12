import socketio
import time
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC as ADC

sio = socketio.Client()
ADC.setup()

#Sensor Pin Set up
GPIO.setup("P9_12", GPIO.IN)
GPIO.setup("P9_14", GPIO.IN)
GPIO.setup("P9_15", GPIO.IN)

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
        # Force Sensor Code
        #BBBW3 Clip 1 (08)
      
        DigitalValue = ADC.read("P9_36")
        AnalogVoltage = (DigitalValue * 1.8) * (2200 / 1200)
        
        
        # Print input value from KeyLock2
        print(GPIO.input("P9_12"), GPIO.input("P9_14"), GPIO.input("P9_15"))
        time.sleep(0.3)
        
        if GPIO.input("P9_12")==1:
            sio.emit('BBBW2Event', {'data': "1st Compartment(Left)"})
            print('Data sent!')
            print("1st Compartment(Left)")
            
        if GPIO.input("P9_14")==1:
            sio.emit('BBBW2Event', {'data': "2st Compartment(Middle)"})
            print('Data sent!')
            print("2st Compartment(Middle)")
            
        if GPIO.input("P9_15")==1:
            sio.emit('BBBW2Event', {'data': "3st Compartment(Right)"})
            print('Data sent!')
            print("2st Compartment(Right)")
            print("3rd Compartment")
            
        #Pot sensor code
        #BBBW3 Clip 2 (08)
      
        DigitalValue = ADC.read("P9_37")
        AnalogVoltage = DigitalValue * 100
        sio.emit('BBBW4Event', {'data': "temp"})
        
        if ADC.read("P9_37") > 0:
            sio.emit('BBBW3Event', {'data': ADC.read("P9_37")})
            print("Digital Value: %f, Analog Voltage: %f" % (DigitalValue, AnalogVoltage))
            time.sleep(0.3)
            
    except:
        print('Unable to transmit data.')
        pass
