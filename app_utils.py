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


class OLED:
    def __init__(self, oled):
        from PIL import Image, ImageDraw, ImageFont
        self.Image = Image
        self.ImageDraw = ImageDraw
        self.ImageFont = ImageFont

        self.Display = oled
        self.FrameBuf = None
        self.state = 'Temperature'
        self.standby_cycle = 1

    def OLED_Display(self, text, multiline=True, coords=(2, 4)):
        ImageObj = self.Image.new("1", (64, 32))
        Draw = self.ImageDraw.Draw(ImageObj)
        Draw.rectangle((0, 0, 64 - 1, 32 - 1), outline=1, fill=0)
        Font = self.ImageFont.load_default()
        if multiline:
            Draw.multiline_text(coords, text, font=Font, fill=1)
        else:
            Draw.text(coords, text, font=Font, fill=1)
        self.Display.image(ImageObj)
        return True

    def TempSetDisplay(self, compartment: int, temperature: int):
        temp = min(max(int(temperature), -25), 60)
        comp = min(max(int(compartment), 1), 3)
        Text = f"-Temp Set-\nBox {comp} ${temp}C"
        return self.OLED_Display(Text)

    def TempDisplay(self, compartment: int, temperature: int):
        temp = min(max(int(temperature), -25), 60)
        comp = min(max(int(compartment), 1), 3)
        Text = f"---Temp---\nBox {comp} ${temp}C"
        return self.OLED_Display(Text)

    def PassDisplay(self, pass_length: str):
        # pass_len = "*" * min(max(pass_length, 0), 4)
        Text = f"---PASS---\n{pass_length:^10s}"
        return self.OLED_Display(Text)

    def AGDisplay(self, status: bool):
        Text = "  Access  \n Granted  " if status else "  Access  \n  Denied  "
        return self.OLED_Display(Text)

    def AlarmDisplay(self):
        Text = "Alarm"
        return self.OLED_Display(Text, multiline=False, coords=(16, 10))

    def TemperatureCycle(self):
        if self.standby_cycle == 4:
            self.standby_cycle = 1
        self.TempDisplay(self.standby_cycle, 0)
        self.standby_cycle += 1

    def ShowImage(self, path):
        ImageObj = self.Image.open(path)
        self.Display.image(ImageObj)

    def ShowDisplay(self):
        self.Display.show()


class KeyInput:
    def __init__(self):
        self.current_key: str = ""
        self.previous_key = ""
        self.waiting = False

    def write_input(self, value) -> None:
        if 0.00 <= value < 0.10:
            self.current_key = "T0"
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

    def getInput(self) -> str:
        if self.waiting and self.previous_key != self.current_key:
            result = self.previous_key
            self.previous_key = self.current_key
            self.waiting = False
            return result
