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


# UI

buffer_layout = Buffer_()  # TM/TC live feed buffer

verbose = Checkbox(text="Verbose", checked=False)


TM_window = Window(
    BufferControl(
        buffer=buffer_layout, focusable=True, input_processors=[FormatText()]
    ),
    wrap_lines=True,
)

verticalline1 = VerticalLine()

watchdog_radio = RadioList(values=[(False, "False"), (True, "True")])
watchdog_cleared = Label(text="")


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
        "data": "skyblue",
    }
)

