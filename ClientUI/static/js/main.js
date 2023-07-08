class ModalDialog {
    constructor(elementID) {
        this.modal = document.getElementById(elementID);
        this.boxID = 0;
        const modal_close = this.modal.querySelector("#modal-close");
        modal_close.addEventListener("click", (e) => {
            this.modal.close();
        })
    }

    setBoxID(box_id, locked, empty, tempSet, tempState) {
        this.boxID = box_id
        this.locked = locked
        this.empty = empty
        this.tempSet = tempSet
        this.tempState = tempState
    }

    #updateModal() {
        const lockIMG = this.modal.querySelector("div#box-state div#lockState div#view-lock-state")
        const lock_text = this.modal.querySelector("div#box-state div#lockState span")

        const boxstateIMG = this.modal.querySelector("div#box-state div#boxState div#view-box-state")
        const boxstate_text = this.modal.querySelector("div#box-state div#boxState span")

        const tempSetIMG = this.modal.querySelector("div#box-temperature div#tempSet div#temp-knob")

        const tempStateIMG = this.modal.querySelector("div#box-temperature div#tempState div#view-temp-state")
        const tempState_text = this.modal.querySelector("div#box-temperature div#tempState span")

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
        knob.setProperty('fnStringToValue', function(string) { return parseInt(string.slice(0, -1)); });
        knob.setProperty('fnValueToString', function(value) { return value.toString()+"°C"; });
        knob.setValue(this.tempSet);
        tempSetIMG.innerHTML = "";
        tempSetIMG.appendChild(knob.node());

        switch (this.tempState) {
            case 0:
                tempStateIMG.style = "background-image: url('/static/images/states/temperature/heater.png')"
                tempState_text.textContent = "Mode: Heater"
                break;

            case 1:
                tempStateIMG.style = "background-image: url('/static/images/states/temperature/Refridgerate_cooler.png')"
                tempState_text.textContent = "Mode: Freezer"
                break;

            case 2:
                tempStateIMG.style = "background-image: url('/static/images/states/temperature/room_temp.png')"
                tempState_text.textContent = "Mode: None"
                break;
        }

        boxID_text.textContent = `Box ${this.boxID}`;
    }

    showModal() {
        this.#updateModal()
        return this.modal.showModal();
    }

}

const projectIMGCanvas = document.getElementById('project-model');
const projectIMGContext = projectIMGCanvas.getContext('2d');
const BoxModal = new ModalDialog("modal-box");


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

        return !!(between(x, rect_x, rect_x + rect_w) && between(y, rect_y, rect_y + rect_h));
    }

    if (isIntersecting(e, 40, 295, 162, 115)) {
        BoxModal.setBoxID(1, true, false, -25, 1);
        console.log("Box 1 is clicked");
    }
    if (isIntersecting(e, 205, 295, 162, 115)) {
        BoxModal.setBoxID(2, true, false, -25, 1);
        console.log("Box 2 is clicked");
    }
    if (isIntersecting(e, 375, 295, 162, 115)) {
        BoxModal.setBoxID(3, true, false, -25, 1);
        console.log("Box 3 is clicked");
    }
    if (isIntersecting(e, 38, 415, 495, 108)) {
        BoxModal.setBoxID(4, true, false, -25, 1);
        console.log("Box 4 is clicked");
    }
    BoxModal.showModal()
})