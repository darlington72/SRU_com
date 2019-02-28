from time import sleep
import socket
import datetime
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
    if args.test or args.loop:
        BD_TM_file = open("BD/BDTC.json", "r")
    else:
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


def write_to_file(file_, data, type):
    if file_ is not None:

        file_.write(
            datetime.datetime.now().strftime("%H:%M:%S.%f")[:-4]
            + f" ## {type} ## "
            + data
            + "\n"
        )


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


class SerialSocket:
    def __init__(self):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_host = conf["socket"]["host"]
        self.socket_port = conf["socket"]["port"]
        self.socket_client = conf["socket"]["client"]

        try:
            self.socket.bind((self.socket_host, self.socket_port))
        except socket.error:
            print(
                "Error while trying to launch socket server. Please check ethernet configuration"
            )
            sys.exit(0)

    def write(self, data):
        if isinstance(data, int):
            self.socket.sendto(bytes([data]), (self.socket_client, self.socket_port))
        else:
            # for i in data:
            print(f"sent {data}")
            self.socket.sendto(data, (self.socket_client, self.socket_port))

    def read(self, size=1) -> bytearray:
        print(f"read called with size {size}")
        data = self.socket.recv(size)
        print(data)
        return data
