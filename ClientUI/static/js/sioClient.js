const socket = io('https://192.168.12.2:someport')

class InternalState {
    constructor() {
        this.box1 = {
            Temp: 0,
            DoorFalse: 0,
            Weight: 0
        };

        this.box2 = {
            Temp: 0,
            DoorFalse: 0,
            Weight: 0
        };

        this.box3 = {
            Temp: 0,
            DoorFalse: 0,
            Weight: 0
        };

        this.box4 = {
            Temp: 0,
            DoorFalse: 0,
            Weight: 0
        };

        this.timeout = 0;
    }

    updateBox(boxID, newState) {
        switch (boxID) {
            case 1:
                this.box1 = {...this.box1, newState};
                break;
            case 2:
                this.box2 = {...this.box2, newState};
                break;
            case 3:
                this.box3 = {...this.box3, newState};
                break;
            case 4:
                this.box4 = {...this.box4, newState};
                break;
        }
    }

    getBox(boxID) {
        switch (boxID) {
            case 1:
                return this.box1;
            case 2:
                 return this.box2;
            case 3:
                 return this.box3;
            case 4:
                 return this.box4;
        }
    }
}

function showToast(message, err=false) {
    Toastify({
        text: message,
        duration: 3000,
        close: true,
        gravity: "bottom",
        position: "right",
        stopOnFocus: true,
        style: {
          background: err ? "FireBrick" : "MediumSpringGreen",
          color: "Snow",
        }
      }).showToast();
}

function socketio_callback(status_code) {
    switch (status_code) {
        case 415:
            showToast('Unable to send message, Invaild act', true)
            break;
        case 501:
            showToast('Unable to send message, Invaild key', true)
            break;
        case 400:
            showToast('Invaild Pin', true)
            break;
    }
}

const STATE = new InternalState();

socket.on('UI_Tx', (RxData) => {
    if (RxData.act === 'update') {
        switch (RxData.key) {
            case 'state':
                STATE.updateBox(RxData.value.BoxID, {
                    Temp: RxData.value.Temp,
                    DoorFalse: RxData.value.DoorFalse,
                    Weight: RxData.value.Weight
                })
                break;
            case 'timeout':
                STATE.timeout = RxData.value
                break;

            case 'alarm':
                STATE.alarm = true
                break;
        }
    }
})

async function sendState(boxID, TempSet, DoorOpen) {
    socket.emit('BBB1_Rx', {
        'act': 'update',
        'key': 'state',
        'value': {
            'BoxID': boxID,
            'Temp': TempSet,
            'DoorOpen': DoorOpen
        }
    }, socketio_callback)
}

function getState() {
    socket.emit('BBB1_Rx', {
        'act': 'get',
        'key': 'state',
        'value': 1
    }, socketio_callback)
    socket.emit('BBB1_Rx', {
        'act': 'get',
        'key': 'state',
        'value': 2
    }, socketio_callback)
    socket.emit('BBB1_Rx', {
        'act': 'get',
        'key': 'state',
        'value': 3
    }, socketio_callback)
    socket.emit('BBB1_Rx', {
        'act': 'get',
        'key': 'state',
        'value': 4
    }, socketio_callback)
}

function sendPIN(prev_pin, new_pin) {
    socket.emit('BBB1_Rx', {
        'act': 'update',
        'key': 'password',
        'value': {
            'prev': prev_pin,
            'new': new_pin
        }
    }, (status_code) => {
        socketio_callback(status_code);
        if (status_code === 200)
            showToast("Pin Changed Successfully")
    })
}

function stopAlarm(pin) {
    socket.emit('BBB1_Rx', {
        'act': 'update',
        'key': 'alarm_pin',
        'value': pin
    }, (status_code) => {
        socketio_callback(status_code);
        if (status_code === 200)
            showToast("Alarm Stop")
    })
}

function reset(pin) {
    socket.emit('BBB1_Rx', {
        'act': 'update',
        'key': 'alarm_pin',
        'value': pin
    }, (status_code) => {
        socketio_callback(status_code);
        if (status_code === 200)
            showToast("Reset Sent Successfully")
    })
}

