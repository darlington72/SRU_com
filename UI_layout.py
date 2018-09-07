# Prompt_toolkit
from prompt_toolkit.layout.layout import Window
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import VerticalLine, HorizontalLine, Label
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit import HTML
from prompt_toolkit_redefinition import (
    Buffer_,
    Checkbox_,
    RadioList_,
    FormatText,
    SelectableList,
)
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.containers import HSplit, VSplit, FloatContainer, Float
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import Frame
from prompt_toolkit.layout.menus import CompletionsMenu
from args import args
from version import __version__
import serial_com
import lib


class UI:
    def __init__(self, ser, lock):

        # TC list and sending
        TC_list = [(_, lib.BD[_]["name"]) for _ in lib.BD if lib.BD[_]["type"] == "TC"]
        self.TC_selectable_list = []

        def TC_send_handler():
            serial_com.send_TC(ser, lock, self.TC_selectable_list)

        self.TC_selectable_list = SelectableList(
            values=TC_list, handler=TC_send_handler
        )

        ######  CLEAR WATCHDOG ######
        self.watchdog_radio = RadioList_(values=[(False, "False"), (True, "True")])
        if args.watchdog:
            self.watchdog_radio.set_value(1)
        self.watchdog_cleared_buffer = Buffer()
        watchdog_cleared = Window(
            BufferControl(buffer=self.watchdog_cleared_buffer, focusable=False)
        )

        ######  CONFIGURATION   #####
        self.verbose = Checkbox_(text="Verbose", checked=args.verbose)
        raw_data_onoff = Checkbox_(text="Raw Data Window", checked=True)

        ######  CREDITS   #####
        credit = Label(
            text=f"   SRU_com - Version {__version__} \n      Author: L.Riviere \n  <laurent.riviere@cnes.fr> "
        )

        ######  TMTC FEED   #####
        verticalline1 = VerticalLine()

        self.buffer_layout = Buffer_()  # TM/TC live feed buffer

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
        raw_serial_buffer = FormattedTextControl(HTML(""), show_cursor=False)
        raw_serial_window = Window(
            content=raw_serial_buffer, height=10, wrap_lines=True
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
                            Frame(title="Clear Watchdog", body=self.watchdog_radio),
                            Frame(title="TC List", body=self.TC_selectable_list),
                            Frame(title="Configuration", body=self.verbose),
                            watchdog_cleared,
                            credit,
                        ],
                        height=D(),
                        width=30,
                    ),
                    verticalline1,
                    HSplit([TM_window, horizontal_line, raw_serial_window]),
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

        self.application = Application(
            layout=Layout(self.root_container),
            key_bindings=self.bindings,
            style=style,
            full_screen=True,
            mouse_support=False,
        )

    def run_app(self):
        self.application.run()
        print("Bye bye.")
        lib.conf_file.close()
        lib.BD_file.close()

