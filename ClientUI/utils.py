import configparser
from typing import Optional
    

class RawConfig:
    def __init__(self, config_name, auto_save=True):
        self.__config__ = configparser.ConfigParser()
        self.__config__.read(config_name)
        self.config_path = config_name
        self.auto_save = auto_save

    def saveConfig(self, internal=False):
        if internal and not self.auto_save:
            return
        with open(self.config_path, "w") as fp:
            self.__config__.write(fp, True)

    def getValue(self, section, key):
        return self.__config__.get(section=section, option=key)

    def writeValue(self, section, key, value):
        self.__config__.set(section=section, option=key, value=value)
        self.saveConfig(internal=True)

    def removeValue(self, section, key):
        self.__config__.remove_option(section=section, option=key)
        self.saveConfig(internal=True)

    def createSection(self, section):
        self.__config__.add_section(section=section)
        self.saveConfig(internal=True)

    def removeSection(self, section):
        self.__config__.remove_section(section=section)
        self.saveConfig(internal=True)

    def load_default(self, default_config: dict):
        if self.__config__.has_section("USER"):
            return
        else:
            self.__config__["DEFAULT"] = default_config
            self.createSection("USER")
            self.saveConfig(internal=True)


class FixedArray:
    def __init__(self, size):
        self.size = size
        self._internal = [0 for i in range(self.size)]

    def add(self, value):
        self._internal.append(value)
        self._internal.pop(0)

    def get(self, index):
        return self._internal[index]

    def getSlice(self, start, stop):
        if (0 <= start < self.size) and (0 <= stop < self.size) and (start < stop):
            return self._internal[start:stop]
        else:
            return None

    def __len__(self):
        return self.size


class KeyInput:
    def __init__(self):
        self.current_key: Optional[str] = None
        self.keyHolding: Optional[str] = None
        self.key_press: Optional[str] = None
        self.keyDown: bool = False

    def write_input(self, value) -> None:
        if 0.00 <= value < 0.10:
            self.current_key = None
        elif 0.16 < value < 0.18:
            self.current_key = "T6"
        elif 0.33 < value < 0.35:
            self.current_key = "T5"
        elif 0.50 < value < 0.52:
            self.current_key = "T4"
        elif 0.67 < value < 0.69:
            self.current_key = "T3"
        elif 0.84 < value < 0.86:
            self.current_key = "T2"
        elif 0.90 < value < 1.10:
            self.current_key = "T1"

        if (self.current_key is not None) and (self.keyHolding is None) and (not self.keyDown):
            self.keyHolding = self.current_key
            self.keyDown = True

        elif (self.current_key is None) and (self.keyHolding is not None) and self.keyDown:
            self.key_press = self.keyHolding
            self.keyHolding = None
            self.keyDown = False

    def getInput(self) -> Optional[str]:
        return self.current_key

    def getKeyPress(self) -> Optional[str]:
        result, self.key_press = self.key_press, None
        return result
