$(document).ready(function () {
    //Initialization and declaration of global variable
    const socket = io.connect('http://192.168.12.1:5000');

    const doorAccessCanvas = document.getElementById("DoorCanvas");
    const doorAccessContext = doorAccessCanvas.getContext("2d");
    const doorOpenImage = document.getElementById("dooropen");
    const doorCloseImage = document.getElementById("doorclose");
    const alarmImage = document.getElementById("alarm")

    let DoorOpenCloseStatus;
    let AlarmStatus = false;

    //Event triggered when python web server received data from BBBW1
    socket.on('WebUIUpdate', function (RxData) {
        let _data = RxData
        if (_data.hasOwnProperty("User_Door")) {
            let update_group = _data["User_Door"]
            if (update_group["action"] === "update") {
                DoorOpenCloseStatus = update_group["value"]
                console.log("Door Status: " + DoorOpenCloseStatus)
            }
        }
        if (_data.hasOwnProperty("AlarmStatus")) {
            let update_group = _data["AlarmStatus"]
            if (update_group["action"] === "update") {
                AlarmStatus = update_group["value"]
                console.log("Alarm Status: " + AlarmStatus)
            }
        }
        updateDoor()
    });

    function updateDoor() {
        doorAccessContext.globalAlpha = 1.0;
        doorAccessContext.clearRect(0, 0, 200, 155);
        console.log("Door Status: " + DoorOpenCloseStatus)
        if (AlarmStatus) {
            doorAccessContext.drawImage(alarmImage, 50, 28);
        } else {
            if (DoorOpenCloseStatus) {
                doorAccessContext.drawImage(doorCloseImage, 50, 28);
            } else {
                doorAccessContext.drawImage(doorOpenImage, 50, 28);
            }
        }
        doorAccessContext.fill();
    }

    function toggleDoor() {
        if (DoorOpenCloseStatus) {
            socket.emit("StateUpdate", {"User_Door": {"action": "update", "value": false}})
            console.log("Door Toggle to open")
        } else {
            socket.emit("StateUpdate", {"User_Door": {"action": "update", "value": true}})
            console.log("Door Toggle to close")
        }
        socket.emit("StateUpdate", {"User_Door": {"action": "get"}})
        socket.emit("StateUpdate", {"AlarmStatus": {"action": "get"}})
    }

    document.getElementById("door").addEventListener("click", toggleDoor);

    socket.emit("StateUpdate", {"User_Door": {"action": "get"}})
    socket.emit("StateUpdate", {"AlarmStatus": {"action": "get"}})
    updateDoor()
});