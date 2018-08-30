# Prompt_toolkit
from prompt_toolkit.layout.layout import Window
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import VerticalLine, HorizontalLine, Label
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit import HTML
from prompt_toolkit_redefinition import Buffer_, Checkbox_, RadioList_, FormatText
from args import args
from version import __version__


buffer_layout = Buffer_()  # TM/TC live feed buffer
verbose = Checkbox_(text="Verbose", checked=args.verbose)
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

horizontal_line = HorizontalLine()
credit = Label(
    text=f"   SRU_com - Version {__version__} \n      Author: L.Riviere \n  <laurent.riviere@cnes.fr> "
)

# raw_serial_buffer = Buffer_()
# raw_serial_window = Window(BufferControl(buffer=raw_serial_buffer, focusable=False, input_processors=[FormatText()]), height=10, wrap_lines=True)

raw_serial_buffer = FormattedTextControl(HTML(""), show_cursor=False)
raw_serial_window = Window(content=raw_serial_buffer, height=10, wrap_lines=True)

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
