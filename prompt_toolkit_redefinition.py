import datetime
import six

# Prompt_toolkit
from prompt_toolkit.filters import to_filter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.layout import Window
from prompt_toolkit.widgets import RadioList, Checkbox, TextArea
from prompt_toolkit.application import get_app
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


class FormatText(Processor):
    def apply_transformation(self, ti):
        fragments = to_formatted_text(HTML(fragment_list_to_text(ti.fragments)))
        return Transformation(fragments)


class Buffer_(Buffer):
    def insert_line(self, data, with_time_tag=True):
        if with_time_tag:
            time_tag = (
                "<grey>"
                + datetime.datetime.now().strftime("%H:%M:%S.%f")[:-4]
                + "</grey>: "
            )
            # datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]
        else:
            time_tag = ""

        self.text += time_tag + data

        if not get_app().layout.has_focus(self):
            self.cursor_position = len(self.text) - len(time_tag + data)


class RadioList_(RadioList):
    def set_value(self, index):
        self._selected_index = index
        self.current_value = self.values[self._selected_index][0]


class Checkbox_(Checkbox):
    def __init__(self, text="", checked=True):
        super().__init__(text)
        self.checked = checked


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
            if self._selected_index == 0:
                self._selected_index = len(self.values) - 1
            else:
                self._selected_index = self._selected_index - 1

        @kb.add("down")
        def _(event):
            if self._selected_index == len(self.values) - 1:
                self._selected_index = 0
            else:
                self._selected_index = self._selected_index + 1

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
