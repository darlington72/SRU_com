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


class SerialTest(object):
    """Replace Serial() for simulation purpose
    
    This class is meant to replace the Serial() class when the flag "-t" (--test) 
    is used on startup. Every byte passed to the write method will be avalaible 
    to be read by the read method. Just as if we looped TX on RX on a real serial 
    link. 

    It allows the software to be tested without the need of any hardware.
    """

    def __init__(self):
        self.buffer = Queue()

    def write(self, data: bytearray):
        for i in data:
            self.buffer.put(i)

    def read(self, size=1) -> bytearray:
        data = bytearray()
        for _ in range(size):
            data += bytearray([self.buffer.get()])

        return data

