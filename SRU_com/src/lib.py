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


class SerialTest:
    """Replace Serial() for simulation purpose

    This class is meant to replace the Serial() class when the flag "-t" (--test)
    is set on startup. Every byte passed to the write method will be available
    to be read by the read method. Just as if we looped TX on RX on a real serial
    link.

    It allows the software to be tested without the need of any hardware.
    """

    def __init__(self):
        # FIFO initialisation
        self.buffer = Queue()

    def write(self, data):
        if isinstance(data, int):
            self.buffer.put(data)
        else:
            for i in data:
                self.buffer.put(i)

    def read(self, size=1) -> bytearray:
        """read method 

        Retreive <size> byte(s) from the FIFO and 
        return them as a bytearray 
        
        Keyword Arguments:
            size {int} -- Number of byte to be read (default: {1})
        
        Returns:
            bytearray -- Data 
        """

        data = bytearray()
        for _ in range(size):
            data += bytearray([self.buffer.get()])

        return data


class SerialSocket:
    """Replace Serial() when SRU_com is launched in socket mode 
    
    This class is meant to replace the Serial() class when the flag "-S" (--socket)
    is set on startup. 
    """

    def __init__(self):

        # Socket init (UDP)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_host = conf["socket"]["host"]
        self.socket_port_TC = conf["socket"]["port_TC"]
        self.socket_port_TM = conf["socket"]["port_TM"]
        self.socket_client = conf["socket"]["client"]

        # A FIFO is also used to store the bytes unused returned by the recv() method
        # See the read() method for more details
        self.buffer = Queue()

        # Socket binding to the IP and PORT for TM
        try:
            self.socket.bind((self.socket_host, self.socket_port_TM))
        except socket.error:
            print(
                "Error while trying to launch socket server. Please check ethernet configuration"
            )
            sys.exit(0)

    def write(self, data):
        """ Send data over the socket link 
        
        Arguments:
            data {int or bytearray} -- Data to be sent over the socket link 
        """

        if isinstance(data, int):
            self.socket.sendto(bytes([data]), (self.socket_client, self.socket_port_TC))
        else:
            self.socket.sendto(data, (self.socket_client, self.socket_port_TC))

    def read(self, size=1) -> bytearray:
        """Return n bytes from the socket 

        A FIFO is used to store the DATA received from the socket 
        because when you call the method socket.recv(n), if there are 
        more than n bytes to read, the excedent will be trashed away and 
        this is not what we want. So we store the unused byte in a FIFO so 
        we can read them later. 
        
        Keyword Arguments:
            size {int} -- Number of byte to read (default: {1})
        
        Returns:
            bytearray -- bytes read from socket 
        """

        # print(f"read called with size {size}")

        # If the FIFO is empty, let's read the data from the socket (blocking)
        if self.buffer.empty():

            # The following line will return even if less than 4096 bytes
            # are received
            data = self.socket.recv(4096)

            # We then put every bytes received into the FIFO
            for byte in data:
                self.buffer.put(byte)

        # Now that we are sure the the FIFO is not empty, we can
        # retreive the data and return them
        data = bytearray()
        for _ in range(size):
            data += bytearray([self.buffer.get()])

        return data
