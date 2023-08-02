from ClientUI import app

SensorConfig = {
    "BBB1": {
        "sensor": ["keypad"],
        "value": {
            "keypad": float,
        }
    },
    "BBB2": {
        "sensor": ["reed1", "reed2", "force1", "force2"],
        "value": {
            "reed1": bool,
            "reed2": bool,
            "force1": float,
            "force2": float
        }
    },
    "BBB3": {
        "sensor": ["pot", "keylock"],
        "value": {
            "pot": float,
            "keylock": [0, 1, 2],
        }
    },
    "BBB4": {
        "sensor": ["infra"],
        "value": {
            "infra": float,
        }
    }
}


def vaildateRxData(board, RxData: dict):
    board_config = SensorConfig.get(board)
    if RxData["sensor"] not in board_config["sensor"]:
        app.logger.warning(f'Unknown Sensor {RxData["sensor"]} sent from {board}')
        return False
    if isinstance(board_config["value"][RxData["sensor"]], list):
        if RxData["value"] not in board_config["value"][RxData["sensor"]]:
            app.logger.warning(f'Unknown Value from Sensor {RxData["sensor"]} sent from {board}')
            return False
    elif isinstance(board_config["value"][RxData["sensor"]], type):
        if not isinstance(RxData["value"], board_config["value"][RxData["sensor"]]):
            app.logger.warning(f'Unknown Value from Sensor {RxData["sensor"]} sent from {board}')
            return False
    return True
