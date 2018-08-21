from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.containers import VSplit, HSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.layout import Layout, Window
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Label, Frame, RadioList, VerticalLine
from pygments.lexers.html import HtmlLexer
from prompt_toolkit import HTML
from prompt_toolkit.layout import FormattedTextControl
from prompt_toolkit.eventloop import use_asyncio_event_loop
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.formatted_text import to_formatted_text
import threading
import serial
from huepy import *
import json
import sys
from time import sleep
import lib
from lib import BD, conf
from serial_com import serial_com_TC, serial_com_TM


def do_exit():
    get_app().exit(result=False)


buffer_layout = Buffer()


TM_window = Window(BufferControl(buffer=buffer_layout, focusable=True))
verticalline1 = VerticalLine()
watchdog_radio = RadioList(values=[(True, "True"), (False, "False")])

TC_list = [BD[_] for _ in BD if BD[_]["type"] == "TC"]

TC_management = "        \n<b>TC list:</b> \n\n"
for TC in TC_list:
    TC_management += TC["name"] + "\n"


root_container = VSplit(
    [
        HSplit(
            [
                Frame(body=Label(text=HTML(TC_management)), title="TC Management", width=30),
                Frame(title="Clear Watchdog", body=watchdog_radio),
            ],
            height=D(),
        ),
        verticalline1,
        TM_window,
    ]
)


# Global key bindings.
bindings = KeyBindings()
bindings.add("tab")(focus_next)
bindings.add("s-tab")(focus_previous)


@bindings.add("c-c", eager=True)
@bindings.add("c-q", eager=True)
def _(event):
    event.app.exit()


style = Style.from_dict(
    {
        "window.border": "#888888",
        "shadow": "bg:#222222",
        "window.border shadow": "#444444",
        "focused  button": "bg:#880000 #ffffff noinherit",
        "radiolist focused": "noreverse",
        "radiolist focused radio.selected": "reverse",
    }
)


application = Application(
    layout=Layout(root_container),
    key_bindings=bindings,
    style=style,
    full_screen=True,
    mouse_support=False,
)


def run_app():
    application.run()
    print("Bye bye.")
    lib.conf_file.close()
    lib.BD_file.close()


if __name__ == "__main__":

    lock = threading.Lock()
    try:
        ser = serial.Serial("/dev/" + conf["COM"]["port"], conf["COM"]["baudrate"])
    except serial.serialutil.SerialException as msg:
        print('Serial error. Please check connection:')
        print(msg)
        print('Both modules usbserial and ftdi_sio should be load (modprobe xx)')
        sys.exit(0)

    thread1 = threading.Thread(target=serial_com_TM, args=(ser, lock, buffer_layout, TM_window))
    thread1.daemon = True
    thread1.start()

    thread1 = threading.Thread(
        target=serial_com_TC, args=(ser, lock, buffer_layout, watchdog_radio)
    )
    thread1.daemon = True
    thread1.start()

    # thread1 = threading.Thread(target=lib.fill_buffer_debug, args=(buffer_layout,))
    # thread1.daemon = True
    # thread1.start()

    run_app()

