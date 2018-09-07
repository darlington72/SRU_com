import threading

from prompt_toolkit.layout.containers import Float, HSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.widgets import Dialog, Label, Button, TextArea
from prompt_toolkit.application.current import get_app
from prompt_toolkit.eventloop import Future, ensure_future, Return, From
import serial_com


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


def do_open_file(ser, root_container):
    def coroutine():
        open_dialog = TextInputDialog(
            title="Application Upload to SRU",
            label_text="Enter the path of the file:",
            completer=PathCompleter(),
        )

        path = yield From(show_dialog_as_float(open_dialog, root_container))

        if path is not None:
            try:
                with open(path, "rb", buffering=0) as f:
                    # show_message("Ok", "It's ok", root_container)
                    data = f.readall()
                    thread_upload = threading.Thread(
                        target=serial_com.upload_app, args=(ser, data, root_container)
                    )
                    thread_upload.start()
            except IOError as e:
                show_message("Error", "{}".format(e), root_container)
                get_app().invalidate()

    ensure_future(coroutine())


def do_conf_TC(ser, root_container):
    def coroutine():
        open_dialog = TextInputDialog(
            title="Application Upload to SRU",
            label_text="Enter the path of the file:",
            completer=PathCompleter(),
        )

        path = yield From(show_dialog_as_float(open_dialog, root_container))

        if path is not None:
            try:
                with open(path, "rb", buffering=0) as f:
                    # show_message("Ok", "It's ok", root_container)
                    data = f.readall()
                    thread_upload = threading.Thread(
                        target=serial_com.upload_app, args=(ser, data, root_container)
                    )
                    thread_upload.start()
            except IOError as e:
                show_message("Error", "{}".format(e), root_container)
                get_app().invalidate()

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
    show_message("About", "about demo", root_container)


def show_message(title, text, root_container, button=True):
    def coroutine():
        dialog = MessageDialog(title, text, button)
        yield From(show_dialog_as_float(dialog, root_container))

    ensure_future(coroutine())


class MessageDialog(object):
    def __init__(self, title, text, button=True):
        self.future = Future()

        def set_done():
            self.future.set_result(None)

        ok_button = (
            [Button(text="OK", handler=(lambda: set_done()))] if button else None
        )

        self.dialog = Dialog(
            title=title,
            body=HSplit([Label(text=text)]),
            buttons=ok_button,
            width=D(preferred=80),
            modal=True,
        )

    def __pt_container__(self):
        return self.dialog


class InfoDialog(object):
    def __init__(self, title, text, root_container):
        dialog = MessageDialog(title, text, button=False)
        self.show_dialog_as_float(dialog, root_container)

    def show_dialog_as_float(self, dialog, root_container):
        " Coroutine. "
        self.float_ = Float(content=dialog)
        root_container.floats.insert(0, self.float_)

        app = get_app()

        app.layout.focus(dialog)

    def remove_dialog_as_float(self, root_container):
        if self.float_ in root_container.floats:
            root_container.floats.remove(self.float_)
