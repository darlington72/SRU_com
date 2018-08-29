# Prompt_toolkit
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.layout import Layout, Window
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import (
    Frame,
    RadioList,
    VerticalLine,
    HorizontalLine,
    Checkbox,
    Label,
    TextArea,
)
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.formatted_text.base import to_formatted_text
from prompt_toolkit.formatted_text.utils import fragment_list_to_text
from prompt_toolkit.layout.margins import ScrollbarMargin, NumberedMargin
from prompt_toolkit import HTML
from prompt_toolkit.document import Document
from prompt_toolkit.widgets.toolbars import SearchToolbar
from prompt_toolkit.layout.processors import (
    PasswordProcessor,
    ConditionalProcessor,
    BeforeInput,
)
from prompt_toolkit.filters import to_filter, Condition
import six
import datetime
from args import args
from version import __version__


class FormatText(Processor):
    def apply_transformation(self, ti):
        fragments = to_formatted_text(HTML(fragment_list_to_text(ti.fragments)))
        return Transformation(fragments)


class Buffer_(Buffer):
    def insert_line(self, data, with_time_tag=True):
        if with_time_tag:
            time_tag = (
                "<grey>"
                + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]
                + "</grey>: "
            )
        else:
            time_tag = ""

        self.text += time_tag + data

        # TODO: integrate cursor position
        # if not get_app().layout.has_focus(TM_window):
        #     buffer_layout._set_cursor_position(len(buffer_layout.text) - 1)
        # app = get_app()

        # focused_before = app.layout.current_window


class RadioList_(RadioList):
    def set_value(self, index):
        self._selected_index = index
        self.current_value = self.values[self._selected_index][0]


class Checkbox_(Checkbox):
    def __init__(self, text="", checked=True):
        super().__init__(text)
        self.checked = checked


class TextArea_(TextArea):
    def __init__(
        self,
        text="",
        multiline=True,
        password=False,
        lexer=None,
        completer=None,
        accept_handler=None,
        focusable=True,
        wrap_lines=True,
        read_only=False,
        width=None,
        height=None,
        dont_extend_height=False,
        dont_extend_width=False,
        line_numbers=False,
        scrollbar=False,
        style="",
        search_field=None,
        preview_search=True,
        prompt="",
    ):

        super().__init__(
            text="",
            multiline=True,
            password=False,
            lexer=None,
            completer=None,
            accept_handler=None,
            focusable=True,
            wrap_lines=True,
            read_only=False,
            width=None,
            height=None,
            dont_extend_height=False,
            dont_extend_width=False,
            line_numbers=False,
            scrollbar=False,
            style="",
            search_field=None,
            preview_search=True,
            prompt="",
        )

        assert isinstance(text, six.text_type)
        assert search_field is None or isinstance(search_field, SearchToolbar)

        if search_field is None:
            search_control = None
        elif isinstance(search_field, SearchToolbar):
            search_control = search_field.control

        self.buffer = Buffer(
            document=Document(text, 0),
            multiline=multiline,
            read_only=read_only,
            completer=completer,
            complete_while_typing=True,
            accept_handler=(lambda buff: accept_handler(buff))
            if accept_handler
            else None,
        )

        self.control = BufferControl(
            buffer=self.buffer,
            lexer=lexer,
            input_processors=[
                ConditionalProcessor(
                    processor=PasswordProcessor(), filter=to_filter(password)
                ),
                BeforeInput(prompt, style="class:text-area.prompt"),
            ],
            search_buffer_control=search_control,
            preview_search=preview_search,
            focusable=focusable,
        )

        if multiline:
            if scrollbar:
                right_margins = [ScrollbarMargin(display_arrows=True)]
            else:
                right_margins = []
            if line_numbers:
                left_margins = [NumberedMargin()]
            else:
                left_margins = []
        else:
            wrap_lines = False  # Never wrap for single line input.
            height = D.exact(1)
            left_margins = []
            right_margins = []

        style = "class:text-area " + style

        self.window = Window(
            height=height,
            width=width,
            dont_extend_height=dont_extend_height,
            dont_extend_width=dont_extend_width,
            content=self.control,
            style=style,
            wrap_lines=wrap_lines,
            left_margins=left_margins,
            right_margins=right_margins,
        )


class SelectableList(object):
    """
    List

    :param values: List of (value, label) tuples.
    """

    def __init__(self, values, handler=None):
        assert isinstance(values, list)
        assert len(values) > 0
        assert all(isinstance(i, tuple) and len(i) == 2 for i in values)

        self.values = values
        self.current_value = values[0][0]
        self._selected_index = 0
        self.handler = handler

        # Key bindings.
        kb = KeyBindings()

        @kb.add("up")
        def _(event):
            self._selected_index = max(0, self._selected_index - 1)

        @kb.add("down")
        def _(event):
            self._selected_index = min(len(self.values) - 1, self._selected_index + 1)

        @kb.add("enter")
        @kb.add(" ")
        def _(event):
            self.current_value = self.values[self._selected_index][0]
            if self.handler is not None:
                self.handler()

        # Control and window.
        self.control = FormattedTextControl(
            self._get_text_fragments, key_bindings=kb, focusable=True
        )

        self.window = Window(
            content=self.control,
            style="class:radio-list",
            right_margins=[ScrollbarMargin(display_arrows=True)],
            dont_extend_height=True,
        )

    def _get_text_fragments(self):
        result = []
        for i, value in enumerate(self.values):
            checked = value[0] == self.current_value
            selected = i == self._selected_index

            style = ""
            if checked:
                style += " class:radio-checked"
            if selected:
                style += " class:radio-selected"

            # result.append((style, '('))

            if selected:
                result.append(("[SetCursorPosition]", ""))

            # if checked:
            #     result.append((style, '*'))
            # else:
            #     result.append((style, ' '))

            # result.append((style, ')'))
            result.append(("class:radio", " "))
            result.extend(to_formatted_text(value[1], style="class:radio"))
            result.append(("", "\n"))

        result.pop()  # Remove last newline.
        return result

    def __pt_container__(self):
        return self.window


# UI

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
credit = Label(text=f'   SRU_com - Version {__version__} \n      Author: L.Riviere \n  <laurent.riviere@cnes.fr> ')

# raw_serial_buffer = Buffer_()
# raw_serial_window = Window(BufferControl(buffer=raw_serial_buffer, focusable=False, input_processors=[FormatText()]), height=10, wrap_lines=True)

raw_serial_buffer = FormattedTextControl(HTML(''), show_cursor=False)
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
