""" SRU_com.py

Entry file for SRU_com 
"""
import threading
import sys
import serial
from prompt_toolkit import HTML

# Custom lib
import src.serial_replacement as serial_replacement
import src.lib as lib
import src.serial_com as serial_com
import src.UI_layout as UI_layout
from src.args import args
from src.update import update


lock = threading.RLock()

if __name__ == "__main__":

    # If SRU_com is launched with the flag -U or --update
    # we launch the auto update routine instead of SRU_com
    if args.update:
        update()
        sys.exit()

    # Serial
    if args.test:
        ser = serial_replacement.SerialTest()
        ser.test = True
    elif args.socket:
        # !! Warning !!
        # When using socket mode, if there's an error in the length of a TM/TC in the BD, SRU_com will be stuck in
        # a infinite loop because there's no timeout on reception
        ser = serial_replacement.SerialSocket()
        ser.test = False
    else:

        try:
            ser = serial.Serial(
                "/dev/" + lib.conf["COM"]["port"], lib.conf["COM"]["baudrate"]
            )
            ser.test = False

        except serial.serialutil.SerialException as msg:
            print("Serial error. Please check connection:")
            print(msg)
            print("Both modules usbserial and ftdi_sio should be loaded (modprobe xx)")
            sys.exit(0)

    # Main UI instance
    ui = UI_layout.UI(ser, lock)

    # Let's wrap serial's read & write to display raw TM/TC exchange
    # in the raw TM/TC window
    ser.write = ui.add_raw_TC_to_window(ser.write)
    ser.read = ui.add_raw_TM_to_window(ser.read)

    # # Thread1 : when watchdog clear is enabled
    # # the thread send the TC clear watchdog everysecond
    # thread1 = threading.Thread(target=serial_com.serial_com_watchdog, args=(ui,))
    # thread1.daemon = True
    # thread1.start()

    # # Thread2: this one deals with TM reception on the uart link
    # # see the function serial_com_TM for details
    # thread2 = threading.Thread(target=serial_com.serial_com_TM, args=(ui,))
    # thread2.daemon = True
    # thread2.start()

    # Finally, lets launch the UI
    ui.run_app()

    # Closing the logging file
    lib.file_logging.close()
