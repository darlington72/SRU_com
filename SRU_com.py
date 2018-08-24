import threading
import sys
import argparse
import serial
import datetime

# Prompt_toolkit
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.containers import *
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.layout import Layout, Window
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import (
    Frame,
    RadioList,
    VerticalLine,
    SelectableList,
    Checkbox,
)
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl

# Custom lib
import version
import lib
from lib import BD, conf
from serial_com import *
import UI
from args import args

lock = threading.Lock()


# TC list and sending
TC_list = [(_, BD[_]["name"]) for _ in BD if BD[_]["type"] == "TC"]
TC_selectable_list = []


def TC_send_handler():
    send_TC(ser, lock, UI.buffer_layout, TC_selectable_list, UI.TM_window)


TC_selectable_list = SelectableList(values=TC_list, handler=TC_send_handler)


root_container = VSplit(
    [
        HSplit(
            [
                Frame(title="Clear Watchdog", body=UI.watchdog_radio),
                Frame(title="TC List", body=TC_selectable_list),
                Frame(title="Configuration", body=UI.verbose),
                UI.watchdog_cleared,
            ],
            height=D(),
            width=30,
        ),
        UI.verticalline1,
        UI.TM_window,
    ]
)


# Global key bindings.
bindings = KeyBindings()


@bindings.add("c-c", eager=True)
@bindings.add("c-q", eager=True)
@bindings.add("q", eager=True)
def _(event):
    event.app.exit()


application = Application(
    layout=Layout(root_container),
    key_bindings=bindings,
    style=UI.style,
    full_screen=True,
    mouse_support=False,
)


def run_app():
    application.run()
    print("Bye bye.")
    lib.conf_file.close()
    lib.BD_file.close()


if __name__ == "__main__":

    # Binding
    bindings.add("tab")(focus_next)
    bindings.add("s-tab")(focus_previous)

    # Serial

    if args.test:
        thread1 = threading.Thread(
            target=lib.fill_buffer_debug, args=(UI.buffer_layout,)
        )
        thread1.daemon = True
        thread1.start()
    else:
        try:
            ser = serial.Serial("/dev/" + conf["COM"]["port"], conf["COM"]["baudrate"])
        except serial.serialutil.SerialException as msg:
            print("Serial error. Please check connection:")
            print(msg)
            print("Both modules usbserial and ftdi_sio should be loaded (modprobe xx)")
            sys.exit(0)

        thread1 = threading.Thread(
            target=serial_com_watchdog,
            args=(
                ser,
                lock,
                UI.buffer_layout,
                UI.TM_window,
                UI.watchdog_radio,
                args.loop,
            ),
        )
        thread1.daemon = True
        thread1.start()

        thread2 = threading.Thread(
            target=serial_com_TM,
            args=(ser, lock, UI.buffer_layout, UI.TM_window, args.loop),
        )
        thread2.daemon = True
        thread2.start()

    run_app()

