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
    Label,
)
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.formatted_text.base import to_formatted_text
from prompt_toolkit.formatted_text.utils import fragment_list_to_text
from prompt_toolkit import HTML
import datetime
from args import args


class FormatText(Processor):
    def __init__(self, char="*"):
        self.char = char

    def apply_transformation(self, ti):

        input_style = Style.from_dict({"aaa": "#ff0066", "bbb": "#44ff00 italic"})

        fragments = to_formatted_text(HTML(fragment_list_to_text(ti.fragments)))
        return Transformation(fragments)


class Buffer_(Buffer):
    def insert_line(self, data):
        time_tag = (
            "<grey>"
            + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]
            + "</grey>"
        )
        self.text += time_tag + ": " + data


class RadioList_(RadioList):
    def set_value(self, index):
        self._selected_index = index
        self.current_value = self.values[self._selected_index][0]


# UI

buffer_layout = Buffer_()  # TM/TC live feed buffer

verbose = Checkbox(text="Verbose", checked=args.verbose)


TM_window = Window(
    BufferControl(
        buffer=buffer_layout, focusable=True, input_processors=[FormatText()]
    ),
    wrap_lines=True,
)

verticalline1 = VerticalLine()

watchdog_radio = RadioList_(values=[(False, "False"), (True, "True")])
if args.watchdog:
    watchdog_radio.set_value(1)

watchdog_cleared_buffer = Buffer()
watchdog_cleared = Window(
    BufferControl(buffer=watchdog_cleared_buffer, focusable=False)
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
    }
)

