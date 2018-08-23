# Prompt_toolkit
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.containers import *
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.layout import Layout, Window
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame, RadioList, VerticalLine, SelectableList, Checkbox
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl

# UI

buffer_layout = Buffer() # TM/TC live feed buffer

verbose = Checkbox(text='Verbose', checked=False)

TM_window = Window(BufferControl(buffer=buffer_layout, focusable=True))

verticalline1 = VerticalLine()

watchdog_radio = RadioList(values=[(False, "False"), (True, "True")])

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

