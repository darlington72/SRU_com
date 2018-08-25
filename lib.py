from time import sleep
import json
import sys
from queue import Queue

try:
    conf_file = open("conf.json", "r")
    conf = json.load(conf_file)
except FileNotFoundError:
    print("Configuration file 'conf.json' not found.")
    sys.exit()

try:
    BD_file = open("BD.json", "r")
    BD = json.load(BD_file)
except FileNotFoundError:
    print("BD file 'conf.json' not found.")
    sys.exit()


def format_frame(*frame):
    frame_hexa = "".join(frame[:-1])
    formatted_frame = f"{frame_hexa:90} {frame[-1]}"
    return formatted_frame


def fill_buffer_debug(buffer):
    while True:
        buffer.text += "TM \n"
        sleep(1)


class SerialTest:
    def __init__(self):
        self.buffer = Queue()

    def write(self, data):
        for i in data:
            self.buffer.put(i)

    def read(self, size=1):
        data = bytearray()
        for _ in range(size):
            data += bytearray([self.buffer.get()])

        return data

