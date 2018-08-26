from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.containers import HSplit, VSplit, Float
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.layout import Layout, Window
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.widgets import (
    Frame,
    RadioList,
    VerticalLine,
    Checkbox,
    TextArea,
    Dialog,
    Label,
    Button,
)
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.application.current import get_app
from prompt_toolkit.eventloop import Future, ensure_future, Return, From


class TextInputDialog(object):
    def __init__(self, title="", label_text="", completer=None):
        self.future = Future()

        def accept_text(buf):
            get_app().layout.focus(ok_button)
            buf.complete_state = None

        def accept():
            self.future.set_result(self.text_area.text)

        def cancel():
            self.future.set_result(None)

        self.text_area = TextArea(
            completer=completer,
            multiline=False,
            width=D(preferred=40),
            accept_handler=accept_text,
        )

        ok_button = Button(text="OK", handler=accept)
        cancel_button = Button(text="Cancel", handler=cancel)

        self.dialog = Dialog(
            title=title,
            body=HSplit([Label(text=label_text), self.text_area]),
            buttons=[ok_button, cancel_button],
            width=D(preferred=80),
            modal=True,
        )

    def __pt_container__(self):
        return self.dialog


def do_open_file(root_container):
    def coroutine():
        global current_path
        open_dialog = TextInputDialog(
            title="Open file",
            label_text="Enter the path of a file:",
            completer=PathCompleter(),
        )

        path = yield From(show_dialog_as_float(open_dialog, root_container))
        current_path = path

        if path is not None:
            pass

    ensure_future(coroutine())


def show_dialog_as_float(dialog, root_container):
    " Coroutine. "
    float_ = Float(content=dialog)
    root_container.floats.insert(0, float_)

    app = get_app()

    focused_before = app.layout.current_window
    app.layout.focus(dialog)
    result = yield dialog.future
    app.layout.focus(focused_before)
    if float_ in root_container.floats:
        root_container.floats.remove(float_)

    raise Return(result)


def do_about(root_container):
    show_message(
        "About", "Text editor demo.\nCreated by Jonathan Slenders.", root_container
    )


def show_message(title, text, root_container):
    def coroutine():
        dialog = MessageDialog(title, text)
        yield From(show_dialog_as_float(dialog, root_container))

    ensure_future(coroutine())


class MessageDialog(object):
    def __init__(self, title, text):
        self.future = Future()

        def set_done():
            self.future.set_result(None)

        ok_button = Button(text="OK", handler=(lambda: set_done()))

        self.dialog = Dialog(
            title=title,
            body=HSplit([Label(text=text)]),
            buttons=[ok_button],
            width=D(preferred=80),
            modal=True,
        )

    def __pt_container__(self):
        return self.dialog
