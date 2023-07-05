from functools import lru_cache
import configparser


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

    @lru_cache(maxsize=10, typed=False)
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