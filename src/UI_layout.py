import binascii
import sys
import serial
from asyncio import get_event_loop
import queue

# Prompt_toolkit
from prompt_toolkit.eventloop import (
    use_asyncio_event_loop,
    run_in_executor,
    call_from_executor,
)
from prompt_toolkit.layout.layout import Window
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import VerticalLine, HorizontalLine, Label
from prompt_toolkit.buffer import Buffer, Document
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit import HTML
from src.prompt_toolkit_redefinition import (
    Buffer_,
    Checkbox_,
    RadioList_,
    FormatText,
    SelectableList,
)
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.containers import (
    HSplit,
    VSplit,
    FloatContainer,
    Float,
    Container,
)
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import Frame
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.application.current import get_app

# Project
from src.args import args
from version import __version__
import src.serial_com as serial_com
import src.lib as lib
from src.lib import conf
import src.float_window as float_window
import src.tools as tools


class UI:
    def __init__(self, ser, lock, file_):

        self.ser = ser
        self.lock = lock
        self.last_TM = queue.Queue(maxsize=1)
        self.file_ = file_
        self.add_data_to_raw_window_enabled = True

        # TC list and sending
        TC_list = [
            (_, lib.BD_TC[_]["name"])
            for _ in lib.BD_TC
            if (
                "hidden" not in lib.BD_TC[_]
                or ("hidden" in lib.BD_TC[_] and lib.BD_TC[_]["hidden"] == False)
            )
        ]
        self.TC_selectable_list = []

        def TC_send_handler():
            if (
                "length" in lib.BD_TC[self.TC_selectable_list.current_value]
                and int(lib.BD_TC[self.TC_selectable_list.current_value]["length"], 16)
                > 0
            ):
                # TC has parameter(s)
                float_window.do_conf_TC(0, [], self)
            else:
                serial_com.send_TC(self.TC_selectable_list.current_value, [], self)

        self.TC_selectable_list = SelectableList(
            values=TC_list, handler=TC_send_handler
        )
        self.last_TC_sent = {
            "frame_bytes": "",
            "frame_str": "",
            "buffer_feed": "",
            "hex_upload": False,
            "hex_file": "",
        }

        ######  WATCHDOG CLEAR ######
        self.watchdog_radio = RadioList_(values=[(False, "False"), (True, "True")])
        if args.watchdog:
            self.watchdog_radio.set_value(1)
        self.watchdog_cleared_buffer = Buffer()
        watchdog_cleared = Window(
            BufferControl(buffer=self.watchdog_cleared_buffer, focusable=False)
        )

        ######      TOOLS       #####
        def tools_handler():
            tools.tools_handler(self)

        self.tools_selectable_list = SelectableList(
            values=tools.tools_list, handler=tools_handler
        )

        ######  CONFIGURATION   #####
        self.verbose = Checkbox_(text="Verbose", checked=args.verbose)
        self.raw_data_onoff = Checkbox_(text="Raw Data Window", checked=True)

        ####  KEYBOARD SHORTCUT ####
        keyboard_shortcuts = Label(
            text=f"<ctrl> + C: quit \n<tab>     : change focus \n<ctrl> + R: re-send last TC \n<ctrl> + P: clear TMTC feed"
        )

        ######  CREDITS   #####
        credit = Label(
            text=f"   SRU_com - Version {__version__} \n      Author: L.Riviere \n  <laurent.riviere@cnes.fr> "
        )

        ######  TMTC FEED   #####
        verticalline1 = VerticalLine()

        self.buffer_layout = Buffer_(read_only=True)  # TM/TC live feed buffer

        TM_window = Window(
            BufferControl(
                buffer=self.buffer_layout,
                focusable=True,
                input_processors=[FormatText()],
            ),
            wrap_lines=True,
        )

        horizontal_line = HorizontalLine()

        ######  RAW DATA   #####
        # self.raw_serial_buffer = FormattedTextControl(HTML(""), show_cursor=False)
        # self.raw_serial_window = Window(
        #     content=self.raw_serial_buffer, height=10, wrap_lines=True
        # )

        self.raw_serial_buffer = Buffer_()
        self.raw_serial_buffer.text_len = 0
        self.raw_serial_window = Window(
            BufferControl(
                buffer=self.raw_serial_buffer,
                focusable=False,
                input_processors=[FormatText()],
            ),
            height=5,
            wrap_lines=True,
        )

        style = Style.from_dict(
            {
                "window.border": "#888888",
                "shadow": "bg:#222222",
                "window.border shadow": "#444444",
                "focused  button": "bg:#880000 #ffffff noinherit",
                "radiolist focused": "noreverse",
                "radiolist focused radio.selected": "reverse",
                "tc": "fg:#ffaf5f",
                "tm": "fg:#ffffb0",
                "syncword": "fg:#247ba0",
                "datalen": "fg:#8ba6a9",
                "tag": "fg:#a7cecb",
                "data": "fg:#f3ffbd",
                "crc": "fg:#247ba0",
                "error": "fg:#af4f54",
            }
        )

        self.root_container = FloatContainer(
            content=VSplit(
                [
                    HSplit(
                        [
                            Frame(title="Watchdog Clear", body=self.watchdog_radio),
                            Frame(title="TC List", body=self.TC_selectable_list),
                            Frame(title="Tools", body=self.tools_selectable_list),
                            Frame(title="Configuration", body=self.verbose),
                            Frame(title="Keyboard shortcuts", body=keyboard_shortcuts),
                            watchdog_cleared,
                            credit,
                        ],
                        height=D(),
                        width=30,
                    ),
                    verticalline1,
                    HSplit([TM_window, horizontal_line, self.raw_serial_window]),
                ]
            ),
            floats=[
                Float(
                    xcursor=True,
                    ycursor=True,
                    content=CompletionsMenu(max_height=16, scroll_offset=1),
                )
            ],
        )

        # Global key bindings.
        self.bindings = KeyBindings()
        # Binding
        self.bindings.add("tab")(focus_next)
        self.bindings.add("s-tab")(focus_previous)

        @self.bindings.add("c-c", eager=True)
        @self.bindings.add("c-q", eager=True)
        # @bindings.add("q", eager=True)
        def _(event):
            event.app.exit()

        @self.bindings.add("c-r", eager=True)
        def send_last_TC_again(event):
            if self.last_TC_sent["frame_bytes"] or self.last_TC_sent["hex_upload"]:
                serial_com.send_TC(
                    self.TC_selectable_list.current_value,
                    None,
                    self,
                    resend_last_TC=True,
                )

        @self.bindings.add("c-p", eager=True)
        def clear_TMTC_feed(event):
            self.buffer_layout.set_document(Document(text=""))
            self.raw_serial_buffer.set_document(Document(text=""))

        self.application = Application(
            layout=Layout(self.root_container),
            key_bindings=self.bindings,
            style=style,
            full_screen=True,
            mouse_support=False,
        )

        self.exit_status = None

    def run_tm_and_watchdog(self):

        # Thread1 : when watchdog clear is enabled
        # the thread send the TC clear watchdog everysecond
        run_in_executor(lambda: serial_com.serial_com_watchdog(self), _daemon=True)

        # Thread2: this one deals with TM reception on the uart link
        # see the function serial_com_TM for details
        run_in_executor(lambda: serial_com.serial_com_TM(self), _daemon=True)

    def run_app(self):
        use_asyncio_event_loop()
        self.run_tm_and_watchdog()
        get_event_loop().run_until_complete(
            self.application.run_async().to_asyncio_future()
        )
        # self.application.run()

        if self.exit_status == "serial":
            print("Serial error.")

        print("Bye bye.")
        lib.conf_file.close()
        lib.BD_TM_file.close()
        lib.BD_TC_file.close()

    def add_data_to_raw_window(self, data, type):

        window_size = (
            self.raw_serial_window.current_width * self.raw_serial_window.height
        )

        if self.raw_serial_buffer.text_len > window_size:
            self.raw_serial_buffer.text = ""
            self.raw_serial_buffer.text_len = 0

        if type == "TC":
            self.raw_serial_buffer.insert_line(
                "<TC>" + data + "</TC>", with_time_tag=False, newline=False
            )
        else:
            data = "".join([format(_, "x").zfill(2) for _ in data]).upper()

            self.raw_serial_buffer.insert_line(
                "<TM>" + data + "</TM>", with_time_tag=False, newline=False
            )

        self.raw_serial_buffer.text_len += len(data)

    def add_raw_TC_to_window(self, func):
        def wrapper(data):
            if isinstance(data, int):
                data_formatted = format(data, "x").zfill(2).upper()
            elif isinstance(data, list):
                data_formatted = format(data[0], "x").zfill(2).upper()
            else:
                data_formatted = binascii.hexlify(data).decode().upper()

            try:
                func(data)
            except serial.SerialException:
                self.exit_status = "serial"
                self.application.exit()

            # 
            if self.add_data_to_raw_window_enabled:
                # self.add_data_to_raw_window(data_formatted, "TC")
                call_from_executor(
                    lambda: self.add_data_to_raw_window(data_formatted, "TC")
                )

        return wrapper

    def add_raw_TM_to_window(self, func):
        def wrapper(size):

            try:
                read = func(size)
            except serial.SerialException:
                self.exit_status = "serial"
                self.application.exit()

            
            if self.add_data_to_raw_window_enabled:
                # self.add_data_to_raw_window(read, "TM")
                call_from_executor(lambda: self.add_data_to_raw_window(read, "TM"))

            return read

        return wrapper

    def clear_last_TM_buffer(self):
        if self.last_TM.full():
            self.last_TM.get()

    def wait_for_TM(self, timeout):
        try:
            return self.last_TM.get(block=True, timeout=timeout)
        except queue.Empty:
            return False

