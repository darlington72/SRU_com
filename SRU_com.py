from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.containers import *
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.layout import Layout, Window
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Label, Frame, RadioList, VerticalLine, SelectableList, Button
from pygments.lexers.html import HtmlLexer
from prompt_toolkit import HTML
from prompt_toolkit.layout import FormattedTextControl
from prompt_toolkit.eventloop import use_asyncio_event_loop
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.formatted_text import to_formatted_text
import prompt_toolkit
import threading
import serial
from huepy import *
import json
import sys
from time import sleep
import argparse
from pprint import pprint
# Custom lib
import lib
from lib import BD, conf
from serial_com import serial_com_TC, serial_com_TM, send_TC

lock = threading.Lock()

'''
Serial
''' 
try:
    ser = serial.Serial("/dev/" + conf["COM"]["port"], conf["COM"]["baudrate"])
except serial.serialutil.SerialException as msg:
    print('Serial error. Please check connection:')
    print(msg)
    print('Both modules usbserial and ftdi_sio should be load (modprobe xx)')
    sys.exit(0)


'''
Parser 
'''
parser = argparse.ArgumentParser(description='SRU Com')
parser.add_argument('-v', '--verbose', action='store_true')
args = parser.parse_args()




'''
UI
'''

def do_exit():
    get_app().exit(result=False)


buffer_layout = Buffer()


TM_window = Window(BufferControl(buffer=buffer_layout, focusable=True))
verticalline1 = VerticalLine()
watchdog_radio = RadioList(values=[(False, "False"), (True, "True")])



TC_list = [(_, BD[_]["name"]) for _ in BD if BD[_]["type"] == "TC"]
TC_selectable_list = []

def TC_send_handler():
    send_TC(ser, lock, buffer_layout, TC_selectable_list, args.verbose)



TC_selectable_list = SelectableList(values=TC_list, handler=TC_send_handler)



root_container = VSplit(
    [
        HSplit(
            [
                Frame(title="Clear Watchdog", body=watchdog_radio),
                Frame(title="TC List", body=TC_selectable_list),
            ],
            height=D(), width=30
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

    thread1 = threading.Thread(target=serial_com_TM, args=(ser, lock, buffer_layout, TM_window, args.verbose))
    thread1.daemon = True
    thread1.start()

    thread2 = threading.Thread(
        target=serial_com_TC, args=(ser, lock, buffer_layout, watchdog_radio, args.verbose)
    )
    thread2.daemon = True
    thread2.start()

    # thread1 = threading.Thread(target=lib.fill_buffer_debug, args=(buffer_layout,))
    # thread1.daemon = True
    # thread1.start()



    run_app()

