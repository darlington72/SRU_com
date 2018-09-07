import threading
import sys
import binascii
import serial
from prompt_toolkit import HTML

# Custom lib
import lib
import serial_com
import UI_layout
from args import args

lock = threading.Lock()


if __name__ == "__main__":

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

    def add_raw_TC_to_window(func):
        def wrapper(data):
            data_formatted = binascii.hexlify(data).decode().upper()

            window_size = (
                UI_layout.raw_serial_window.current_width
                * UI_layout.raw_serial_window.height
            )

            if UI_layout.raw_serial_window.text_len > window_size:
                UI_layout.raw_serial_buffer.text = HTML(
                    "<TC>" + data_formatted + "</TC>"
                )
                UI_layout.raw_serial_window.text_len = len(data_formatted)
            else:
                UI_layout.raw_serial_buffer.text += HTML(
                    "<TC>" + data_formatted + "</TC>"
                )
                UI_layout.raw_serial_window.text_len += len(data_formatted)

            func(data)

        return wrapper

    def add_raw_TM_to_window(func):
        def wrapper(size):

            read = func(size)

            read_formatted = "".join([format(_, "x") for _ in read]).upper().zfill(2)

            window_size = (
                UI_layout.raw_serial_window.current_width
                * UI_layout.raw_serial_window.height
            )

            if UI_layout.raw_serial_window.text_len > window_size:
                UI_layout.raw_serial_buffer.text = HTML(
                    "<TM>" + read_formatted + "</TM>"
                )
                UI_layout.raw_serial_window.text_len = len(read_formatted)
            else:
                UI_layout.raw_serial_buffer.text += HTML(
                    "<TM>" + read_formatted + "</TM>"
                )
                UI_layout.raw_serial_window.text_len += len(read_formatted)

            return read

        return wrapper

    ser.write = add_raw_TC_to_window(ser.write)
    ser.read = add_raw_TM_to_window(ser.read)

    thread1 = threading.Thread(target=serial_com.serial_com_watchdog, args=(ser, lock))
    thread1.daemon = True
    thread1.start()

    thread2 = threading.Thread(target=serial_com.serial_com_TM, args=(ser, lock))
    thread2.daemon = True
    thread2.start()

    UI_instance = UI_layout.UI(ser, lock)
    UI_instance.run_app()
