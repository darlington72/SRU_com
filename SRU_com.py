import threading
import sys
import serial
from prompt_toolkit import HTML

# Custom lib
import lib
import serial_com
import UI_layout
from args import args
from update import update

lock = threading.Lock()


if __name__ == "__main__":

    if args.update:
        update()
        sys.exit()

    # Serial
    if args.test:
        ser = lib.SerialTest()
    else:

        try:
            ser = serial.Serial(
                "/dev/" + lib.conf["COM"]["port"], lib.conf["COM"]["baudrate"]
            )

        except serial.serialutil.SerialException as msg:
            print("Serial error. Please check connection:")
            print(msg)
            print("Both modules usbserial and ftdi_sio should be loaded (modprobe xx)")
            sys.exit(0)

    ui = UI_layout.UI(ser, lock)

    # Let's wrap serial's read & write to display raw TM/TC exchange
    # in the raw TM/TC window
    ser.write = ui.add_raw_TC_to_window(ser.write)
    ser.read = ui.add_raw_TM_to_window(ser.read)

    thread1 = threading.Thread(
        target=serial_com.serial_com_watchdog, args=(ui, ser, lock)
    )
    thread1.daemon = True
    thread1.start()

    thread2 = threading.Thread(target=serial_com.serial_com_TM, args=(ui, ser, lock))
    thread2.daemon = True
    thread2.start()

    ui.run_app()
