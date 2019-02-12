from time import sleep
import json
import sys
from queue import Queue
from src.args import args

try:
    conf_file = open("conf.json", "r")
    conf = json.load(conf_file)
except FileNotFoundError:
    print("Configuration file 'conf.json' not found.")
    sys.exit()

try:
    BD_TM_file = open("BD/BDTM.json", "r")
    BD_TM = json.load(BD_TM_file)
except FileNotFoundError:
    print("BDTM file not found.")
    sys.exit()

try:
    BD_TC_file = open("BD/BDTC.json", "r")
    BD_TC = json.load(BD_TC_file)
except FileNotFoundError:
    print("BDTC file not found.")
    sys.exit()


def compute_CRC(frame):
    crc_poly = 0xD5
    crc = 0

    for byte in frame:
        for _ in range(8):
            if (byte & 0x80) ^ (crc & 0x80):
                crc = (crc << 1) ^ crc_poly
            else:
                crc = crc << 1
            byte = byte << 1

    return crc % (2 ** 8)


def compute_CRC_hex(hex_list, ui=None):
    CRC = ""

    for line in hex_list:
        try:
            if line[0] == ":":
                length = int(line[1:3], 16)
                CRC += line[9 : 9 + (length * 2)]

        except IndexError:
            pass

    CRC = CRC.ljust(int(conf["hex_upload"]["max_size_flash_app"]) * 2, "F")
    # ui.buffer_layout.insert_line(f"{CRC}\n")

    CRC = bytearray.fromhex(CRC)
    CRC = compute_CRC(CRC)
    CRC = hex(CRC)[2:]
    return CRC.upper()


def format_frame(*frame):
    frame_hexa = "".join(frame[:-1])
    formatted_frame = f"{frame_hexa:95} {frame[-1]}"
    return formatted_frame


def write_to_file(file_, line):
    if file_ is not None:
        file_.write(line)


class SerialTest:
    """Replace Serial() for simulation purpose

    This class is meant to replace the Serial() class when the flag "-t" (--test)
    is used on startup. Every byte passed to the write method will be available
    to be read by the read method. Just as if we looped TX on RX on a real serial
    link.

    It allows the software to be tested without the need of any hardware.
    """

    def __init__(self):
        self.buffer = Queue()

    def write(self, data):
        if isinstance(data, int):
            self.buffer.put(data)
        else:
            for i in data:
                self.buffer.put(i)

    def read(self, size=1) -> bytearray:
        data = bytearray()
        for _ in range(size):
            data += bytearray([self.buffer.get()])

        return data

