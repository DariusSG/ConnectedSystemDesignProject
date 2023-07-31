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

class InternalState {
    constructor() {
        this.box1 = {
            Temp: 0,
            DoorOpen: false,
            Weight: 0
        };

        this.box2 = {
            Temp: 0,
            DoorOpen: false,
            Weight: 0
        };

        this.box3 = {
            Temp: 0,
            DoorOpen: false,
            Weight: 0
        };

        this.box4 = {
            Temp: 0,
            DoorOpen: false,
            Weight: 0
        };

        this.timeout = 0;
        this.alarm = false
    }

    updateBox(boxID, newState) {
        switch (boxID) {
            case 1:
                if ((newState.Weight - this.box1.Weight) > 10)
                    showToast("Weight Increase on Box 1")
                this.box1 = newState;
                break;
            case 2:
                if ((newState.Weight - this.box2.Weight) > 10)
                    showToast("Weight Increase on Box 2")
                this.box2 = newState;
                break;
            case 3:
                if ((newState.Weight - this.box3.Weight) > 10)
                    showToast("Weight Increase on Box 3")
                this.box3 = newState;
                break;
            case 4:
                if ((newState.Weight - this.box4.Weight) > 10)
                    showToast("Weight Increase on Box 4")
                this.box4 = newState;
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
        case 200:
            showToast('Command Executed Successfully', false)
            break;
    }
}