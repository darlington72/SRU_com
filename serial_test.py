import serial 
from huepy import *
from threading import Thread
from time import sleep
import sys
import json



def serial_com():
    with open("BD.json", "r") as read_file:
        BD = json.load(read_file)
        # print(BD['12340000']['name'])

        with serial.Serial('/dev/ttyUSB0', 115200) as ser:

            print(que('Waiting for sync word'))
            while not ser.read(2).hex() in ('1234', '4321'):
                pass

            print(good('Sync word found!'))
            first_frame_data_lenght = int.from_bytes(ser.read(1), 'big')
            # ser.read(1 + 2)
            ser.read(first_frame_data_lenght + 2)

            while True:
                    *sync_word, data_lenght = ser.read(3) # for no reason ser.read returns int here..
                    sync_word = [format(_ , 'x') for _ in sync_word]

                    tag, *data, CRC = [format(_, 'x') for _ in ser.read(data_lenght + 2)]

                    frame = ''.join(sync_word) + ' ' + format(data_lenght, 'x') + ' ' + tag + ' ' + ''.join(data) + ' ' + CRC

                    

                    print(frame + ' ' + BD[tag]['name'])



def print_other():
    while True:
        # print(info('Other'))
        sleep(0.5)


if __name__ == '__main__':
    try:
        thread1 = Thread(target=serial_com)
        thread1.daemon = True
        thread1.start()

        print_other()

    except KeyboardInterrupt:
        sys.exit(0)