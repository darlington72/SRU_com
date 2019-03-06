""" serial_replacement.py

By default, SRU_com uses a serial (UART) link to communicate with 
the SRU board. Two others options are proposed:
- Test mode: used for test/developpment. In this loop mode every byte written is 
    immediately available for read. No hardware is needed, everything happens in 
    SRU_com
- Socket mode: used to communicate with the zynq over ethernet. In this mode, 
    the zynq acts as a gateway or man in the middle between SRU_com and the SRU board 

The following classes act as a dropped-in replacement for the serial class

"""
import socket
import sys
from queue import Queue, Empty
from src.lib import conf


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
        self.timeout = None

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
        try:
            for _ in range(size):
                data += bytearray([self.buffer.get(timeout=self.timeout)])
        except Empty:
                data = bytearray()

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
