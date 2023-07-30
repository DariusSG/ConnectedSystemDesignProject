const socket = io('http://192.168.12.2:5000')
let STATE = new InternalState();

const overlay = document.querySelector("#overlay");

socket.on('UI_Tx', (RxData) => {
    if (RxData.act === 'update') {
        switch (RxData.key) {
            case 'state':
                console.log(RxData.value.boxID, {
                    Temp: RxData.value.Temp,
                    DoorOpen: RxData.value.DoorOpen,
                    Weight: RxData.value.Weight
                });
                STATE.updateBox(RxData.value.boxID, {
                    Temp: RxData.value.Temp,
                    DoorOpen: RxData.value.DoorOpen,
                    Weight: RxData.value.Weight
                })
                break;
            case 'timeout':
                STATE.timeout = RxData.value
                break;

            case 'alarm':
                STATE.alarm = true
                displayAlarm()
                break;
        }
    }
})

function SIOsendState(boxID, TempSet, DoorOpen) {
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

function SIOgetState() {
    socket.emit('BBB1_Rx', {
        'act': 'get',
        'key': 'state',
        'value': 1
    })
    socket.emit('BBB1_Rx', {
        'act': 'get',
        'key': 'state',
        'value': 2
    })
    socket.emit('BBB1_Rx', {
        'act': 'get',
        'key': 'state',
        'value': 3
    })
    socket.emit('BBB1_Rx', {
        'act': 'get',
        'key': 'state',
        'value': 4
    })
}

function SIOsendPIN(prev_pin, new_pin) {
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

function ResetPIN(pin, content) {
    const pin_container = content.querySelector('#pin_input_container');
    const new_pin = pin_container.getAttribute('pin-input');
    SIOsendPIN(pin, new_pin);
}

function SIOstopAlarm(pin) {
    socket.emit('BBB1_Rx', {
        'act': 'get',
        'key': 'alarm_pin',
        'value': pin
    }, (status_code) => {
        socketio_callback(status_code);
        if (status_code === 200)
            showToast("Alarm Stop")
    })
}

function SIOreset(pin) {
    socket.emit('BBB1_Rx', {
        'act': 'get',
        'key': 'alarm_pin',
        'value': pin
    }, (status_code) => {
        socketio_callback(status_code);
        if (status_code === 200)
            showToast("Reset Sent Successfully")
    })
}

function SIOChangeTimeout(pin, val) {
    socket.emit('BBB1_Rx', {
        'act': 'update',
        'key': 'timeout',
        'value': {
            'pin': pin,
            'timeout': val
        }
    }, (status_code) => {
        socketio_callback(status_code);
        if (status_code === 200)
            showToast("Reset Sent Successfully")
    })
}

function ChangeTimeout(pin, content) {
    const timeout_input = content.querySelector('#lock-timeout');
    const timeout_value = timeout_input.value;
    SIOChangeTimeout(pin,timeout_value);
}

class ModalDialog {
    constructor(elementID) {
        this.modal = document.getElementById(elementID);
        this.boxID = 0;
        const modal_close = this.modal.querySelector("#modal-close");
        modal_close.addEventListener("click", () => this.modal.close());

        const modal_save = this.modal.querySelector("#boxSave");
        modal_save.addEventListener("click", () => this.#saveConfig());
    }

    setBoxID(box_id) {
        this.boxID = box_id
        let { Temp, DoorOpen, Weight} = STATE.getBox(box_id);
        this.locked = !DoorOpen;
        this.empty = (Weight < 10);
        this.tempSet = Temp;
    }

    #saveConfig() {
        console.log("Hello");
        SIOsendState(this.boxID, this.tempSet, !this.locked);
    }

    #updateTempState(modal, tempSet) {
        function between(val, min, max) {
            return val >= min && val <= max;
        }

        const tempStateIMG = modal.querySelector("div#box-temperature div#tempState div#view-temp-state")
        const tempState_text = modal.querySelector("div#box-temperature div#tempState span")

        if (between(tempSet, -25, -5)) {
            tempStateIMG.style = "background-image: url('/static/images/states/temperature/Refridgerate_cooler.png')"
            tempState_text.textContent = "Mode: Freezer"
        }
        else if (between(tempSet, -6, 12)) {
            tempStateIMG.style = "background-image: url('/static/images/states/temperature/Refridgerate_cooler.png')"
            tempState_text.textContent = "Mode: Refrigerate"
        }
        else if (between(tempSet, 13, 24)) {
            tempStateIMG.style = "background-image: url('/static/images/states/temperature/room_temp.png')"
            tempState_text.textContent = "Mode: Off"
        }
        else if (between(tempSet, 24, 60)) {
            tempStateIMG.style = "background-image: url('/static/images/states/temperature/heater.png')"
            tempState_text.textContent = "Mode: Heater"
        }
    }

    #updateModal() {
        const lockIMG = this.modal.querySelector("div#box-state div#lockState div#view-lock-state")
        const lock_text = this.modal.querySelector("div#box-state div#lockState span")

        const boxstateIMG = this.modal.querySelector("div#box-state div#boxState div#view-box-state")
        const boxstate_text = this.modal.querySelector("div#box-state div#boxState span")

        const tempSetIMG = this.modal.querySelector("div#box-temperature div#tempSet div#temp-knob")

        const boxID_text = this.modal.querySelector("div#box-overview div#boxView span");

        if (this.locked){
            lockIMG.style = "background-image: url('/static/images/lockModels/locked.png')"
            lock_text.textContent = "Locked"
        } else {
            lockIMG.style = "background-image: url('/static/images/lockModels/unlocked.png')"
            lock_text.textContent = "Unlocked"
        }

        if (this.empty){
            boxstateIMG.style = "background-image: url('/static/images/states/compartments/box.png')"
            boxstate_text.textContent = "Empty"
        } else {
            boxstateIMG.style = "background-image: url('/static/images/states/compartments/item_in_box.png')"
            boxstate_text.textContent = "Item Present"
        }

        const knob = pureknob.createKnob(150, 150);
        knob.setProperty('angleStart', -0.75 * Math.PI);
        knob.setProperty('angleEnd', 0.75 * Math.PI);
        knob.setProperty('colorFG', '#88ff88');
        knob.setProperty('trackWidth', 0.4);
        knob.setProperty('valMin', -25);
        knob.setProperty('valMax', 65);
        knob.setProperty('fnStringToValue', function(string) { return parseInt(/^-?\d*$/g.exec(string)[0]); });
        knob.setProperty('fnValueToString', function(value) { return value.toString()+"°C"; });
        knob.setValue(this.tempSet);
        tempSetIMG.replaceChildren(knob.node());
        knob.addListener((knob, value) => {
            this.tempSet = value;
            this.#updateTempState(this.modal, this.tempSet);
        });

        this.#updateTempState(this.modal, this.tempSet)

        boxID_text.textContent = `Box ${this.boxID}`;

    }

    showModal() {
        this.#updateModal()
        return this.modal.showModal();
    }
}

class NavbarDialog {
    constructor(elementID) {
        this.modal = document.getElementById(elementID);
        this.modal_content = this.modal.querySelector('#content');
        this.modal_title = this.modal.querySelector('#title');
        this.command_func = null;

        const modal_close = this.modal.querySelector("#modal-close");
        modal_close.addEventListener("click", () => this.closeModal());

        this.modal_execute = this.modal.querySelector("#modal-execute");
        this.modal_execute.addEventListener("click", () => this.executeCommand());

        const pin_container = this.modal.querySelectorAll('#pin_input_container');
        pin_container.forEach((container, _) => {
            const pin_input = container.querySelectorAll('#pin_input');
            pin_input.forEach((num, index) => {
                num.dataset.id = index.toString();

                num.addEventListener('mousewheel', (e)=>{
                    e.preventDefault();
                })

                num.addEventListener('keyup', (e) => {
                    if (num.value.length === 1) {
                        if (pin_input[pin_input.length - 1].value.length !== 1)
                            pin_input[parseInt(num.dataset.id) + 1].focus()
                        else {
                            let pin = "";
                            pin_input.forEach((num, _) => {
                                pin += num.value.toString()
                            });
                            container.setAttribute('pin-input', pin);
                        }

                    } else {
                        console.log(e);
                        if (e.key === 'Backspace') {
                            if (pin_input[pin_input.length - 1].value.length !== 1)
                                pin_input[parseInt(num.dataset.id) - 1].focus()
                        }
                    }
                })
            })
        })
    }

    setModal(num) {
        switch (num) {
            case 1:
                this.modal_title.textContent = "Lock Timeout";
                this.modal_content.innerHTML = (
                    '<p>^^^ Enter Your PIN Above ^^^</p>\n' +
                    '<p>Enter Lock Timeout in Seconds:</p>\n' +
                    '<input type="number" id="lock-timeout" min="10" max="60" value="10" required>'
                );
                this.modal_execute.textContent = "Change";
                this.command_func = ChangeTimeout;
                return
            case 2:
                this.modal_title.textContent = "Calibration";
                this.modal_content.innerHTML = (
                    '<p>^^^ Enter Your PIN Above to Reset ^^^</p>'
                );
                this.modal_execute.textContent = "Calibrate";
                this.command_func = SIOreset;
                return
            case 3:
                this.modal_title.textContent = "Reset PIN";
                this.modal_content.innerHTML = (
                    '<p>^^^ Enter Your Old PIN Above ^^^</p>'+
                    '<div id="pin_input_container">\n' +
                    '<input type="number" id="pin_input" maxlength="1" min="1" max="6" required>\n' +
                    '<input type="number" id="pin_input" maxlength="1" min="1" max="6" required>\n' +
                    '<input type="number" id="pin_input" maxlength="1" min="1" max="6" required>\n' +
                    '<input type="number" id="pin_input" maxlength="1" min="1" max="6" required>\n' +
                    '</div>'+
                    '<p>^^^ Enter Your New PIN Above ^^^</p>'
                );
                this.modal_execute.textContent = "Reset";
                this.command_func = ResetPIN
                return
            case 4:
                this.modal_title.textContent = "Reset Alarm";
                this.modal_content.innerHTML = (
                    '<p>^^^ Enter Your PIN Above to Reset ^^^</p>'
                );
                this.modal_execute.textContent = "Reset";
                this.command_func = SIOstopAlarm;
                return
            case 5:
                this.modal_title.textContent = "Lock / Unlock";
                this.modal_content.innerHTML = (
                    '<p>^^^ Enter Your PIN Above ^^^</p>'
                );
                this.modal_execute.textContent = "Lock / Unlock";
                return
        }
    }

    executeCommand() {
        const pin_input = this.modal.querySelectorAll('#pin_input_container')[0].cloneNode(true);
        let pin = pin_input.getAttribute('pin-input');
        this.command_func(pin, this.modal_content.cloneNode(true))
        this.closeModal()
    }

    closeModal() {
        const pin_input = this.modal.querySelectorAll('#pin_input_container');
        pin_input[0].removeAttribute('pin-input');
        const clear_input = pin_input[0].querySelectorAll('#pin_input');
        clear_input.forEach((num, _) => {
            num.value = '';
        })
        this.modal_content.innerHTML = '';
        this.modal.close()
    }

    showModal() {
        const pin_container = this.modal.querySelectorAll('#pin_input_container');
        pin_container.forEach((container, index) => {
            if (index === 0) {
                container.removeAttribute('pin-input');
                const clear_input = container.querySelectorAll('#pin_input');
                clear_input.forEach((num, _) => {
                    num.value = '';
                })
                return
            }
            const pin_input = container.querySelectorAll('#pin_input');
            pin_input.forEach((num, index) => {
                num.dataset.id = index.toString();

                num.addEventListener('mousewheel', (e)=>{
                    e.preventDefault();
                })

                num.addEventListener('keyup', (e) => {
                    if (num.value.length === 1) {
                        if (pin_input[pin_input.length - 1].value.length !== 1)
                            pin_input[parseInt(num.dataset.id) + 1].focus()
                        else {
                            let pin = "";
                            pin_input.forEach((num, _) => {
                                pin += num.value.toString()
                            });
                            container.setAttribute('pin-input', pin);
                        }

                    } else {
                        console.log(e);
                        if (e.key === 'Backspace') {
                            if (pin_input[pin_input.length - 1].value.length !== 1)
                                pin_input[parseInt(num.dataset.id) - 1].focus()
                        }
                    }
                })
            })
        })
        return this.modal.showModal();
    }
}

const BoxModal = new ModalDialog("modal-box");
const navbarModal = new NavbarDialog("navbar-box");
const projectIMGCanvas = document.getElementById('project-model');
const projectIMGContext = projectIMGCanvas.getContext('2d');

const lock_timout = document.querySelector('#navbar-cell-1');
const reset_calib = document.querySelector('#navbar-cell-2');
const pin_change = document.querySelector('#navbar-cell-3');

function displayAlarm() {
    const alarm = overlay.querySelector('#alarm');
    overlay.classList.add("display");
	alarm.classList.add("display");
    overlay.addEventListener('click', hideAlarm)
    // to stop loading after some time
    setTimeout(() => {
        const alarm = overlay.querySelector('#alarm');
        overlay.classList.remove("display");
        alarm.classList.remove("display");
    }, 50000);
}

function hideAlarm() {
    navbarModal.setModal(4);
    navbarModal.showModal();
    const alarm = overlay.querySelector('#alarm');
    overlay.classList.remove("display");
	alarm.classList.remove("display");
    overlay.removeEventListener('click', hideAlarm)
}

function loadImage(href, dx, dy, scale=1) {
    const image = new Image(60,45);
    image.src = href;
    image.onload = function drawImage() {
        projectIMGCanvas.width = this.naturalWidth * scale;
        projectIMGCanvas.height = this.naturalHeight * scale;

        projectIMGContext.drawImage(this, dx, dy, projectIMGCanvas.width, projectIMGCanvas.height);
    }
    return image;
}

loadImage("/static/images/projectModels/main_box.png", 0, 0, 0.8)

projectIMGCanvas.addEventListener('click', function(e) {
    function isIntersecting(e, rect_x, rect_y, rect_w, rect_h) {
        function between(val, min, max) {
            return val >= min && val <= max;
        }

        const rect = projectIMGCanvas.getBoundingClientRect()
        const x = e.clientX - rect.left
        const y = e.clientY - rect.top
        console.log(x,y);
        return !!(between(x, rect_x, rect_x + rect_w) && between(y, rect_y, rect_y + rect_h));
    }

    isIntersecting(e, 0,0,0,0);

    if (isIntersecting(e, 5, 142, 120, 85)) {
        BoxModal.setBoxID(1);
        console.log("Box 1 is clicked");
    }
    if (isIntersecting(e, 135, 140, 120, 85)) {
        BoxModal.setBoxID(2);
        console.log("Box 2 is clicked");
    }
    if (isIntersecting(e, 262, 140, 120, 85)) {
        BoxModal.setBoxID(3);
        console.log("Box 3 is clicked");
    }
    if (isIntersecting(e, 5, 235, 375, 90)) {
        BoxModal.setBoxID(4);
        console.log("Box 4 is clicked");
    }
    BoxModal.showModal()
})

lock_timout.addEventListener('click', ()=>{
    navbarModal.setModal(1)
    navbarModal.showModal()
})

reset_calib.addEventListener('click', ()=>{
    navbarModal.setModal(2)
    navbarModal.showModal()
})

pin_change.addEventListener('click', ()=>{
    navbarModal.setModal(3)
    navbarModal.showModal()
})

const overviewModal = document.getElementById('overview');
const box1_overviewModal = overviewModal.querySelector('#box-overview-1');
const box2_overviewModal = overviewModal.querySelector('#box-overview-2');
const box3_overviewModal = overviewModal.querySelector('#box-overview-3');
const box4_overviewModal = overviewModal.querySelector('#box-overview-4');

function bindOverviewModal(boxID, modal) {
    const lockIMG = modal.querySelector('#toggle-lock');
    lockIMG.addEventListener('click', () => {
        navbarModal.setModal(5);
        navbarModal.command_func = () => {
            let {Temp, DoorOpen, Weight} = STATE.getBox(boxID);
            SIOsendState(boxID, Temp, !DoorOpen);
        };
        navbarModal.showModal();
    });
}

bindOverviewModal(1, box1_overviewModal);
bindOverviewModal(2, box2_overviewModal);
bindOverviewModal(3, box3_overviewModal);
bindOverviewModal(4, box4_overviewModal);

function updateOverview() {
    function updateState(boxID, modal) {
        const tempstate = modal.querySelector('#tempstate');
        const lockstate = modal.querySelector('#lockstate');
        const lockIMG = modal.querySelector('#toggle-lock');

        let {Temp, DoorOpen, Weight} = STATE.getBox(boxID);
        DoorOpen = true;
        tempstate.textContent = Temp.toString()+"°C";
        lockstate.textContent = DoorOpen ? "Unlocked" : "Locked";
        lockIMG.style = `background-image: url(\"/static/images/lockModels/${(DoorOpen ? "unlocked" : "locked")}.png\")`
    }
    updateState(1, box1_overviewModal);
    updateState(2, box2_overviewModal);
    updateState(3, box3_overviewModal);
    updateState(4, box4_overviewModal);
}

let STATEUPDATE = setInterval(() => {
    SIOgetState();
    updateOverview();
}, 1000);