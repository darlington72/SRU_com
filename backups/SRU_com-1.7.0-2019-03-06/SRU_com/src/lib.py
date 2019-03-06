from time import sleep
import datetime
import json
import sys
from src.args import args

try:
    conf_file = open("conf.json", "r")
    conf = json.load(conf_file)
except FileNotFoundError:
    print("Configuration file 'conf.json' not found.")
    sys.exit()

try:
    if args.test or args.loop:
        BD_TM_file = open(conf["BD_path"]["TC"], "r")
    else:
        BD_TM_file = open(conf["BD_path"]["TM"], "r")

    BD_TM = json.load(BD_TM_file)
except FileNotFoundError:
    print("BDTM file not found.")
    sys.exit()

try:
    BD_TC_file = open(conf["BD_path"]["TC"], "r")
    BD_TC = json.load(BD_TC_file)
except FileNotFoundError:
    print("BDTC file not found.")
    sys.exit()


def compute_CRC(frame):
    """Compute the CRC of <frame>
    
    Arguments:
        frame {str} -- Frame in hex string 
    
    Returns:
        [str] -- Hex representation of the CRC (without the 0x)
    """

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


def compute_CRC_hex(hex_list):
    """Compute the CRC of an hex file 
    
    Arguments:
        hex_list {list of line} -- Liste of each line of the hex file 
    
    Returns:
        [str] -- Hex representation of the CRC (without the 0x)
    """

    CRC = ""

    for line in hex_list:
        try:
            if line[0] == ":":
                length = int(line[1:3], 16)
                CRC += line[9 : 9 + (length * 2)]

        except IndexError:
            pass

    CRC = CRC.ljust(int(conf["hex_upload"]["max_size_flash_app"]) * 2, "F")

    CRC = bytearray.fromhex(CRC)
    CRC = compute_CRC(CRC)
    CRC = hex(CRC)[2:]
    return CRC.upper()


def format_frame(*frame):
    frame_hexa = "".join(frame[:-1])
    formatted_frame = f"{frame_hexa:95} {frame[-1]}"
    return formatted_frame


class FileLogging:
    """Deals with file logging 
    """

    def __init__(self, _file):
        """Open the file if needed 
        
        Arguments:
            _file {str} -- path to the file 
        """

        # We open the file in "append" mode
        self._file = open(_file + ".txt", mode="a") if _file else None

    def write(self, text):
        """Write the text to the file if 
        a file was openned 
        
        Arguments:
            text {str} -- String to be added 
        """

        if self._file is not None:
            self._file.write(text)

    def close(self):
        """Close the file if it was openned before 
        """

        if self._file is not None:
            self._file.close()


# If SRU_com is launched with the flag -f or --file
# we open a file and write every TM/TC into it
file_logging = FileLogging(args.file)