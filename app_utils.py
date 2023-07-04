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