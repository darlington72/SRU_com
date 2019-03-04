import threading
import sys
import asyncio
from time import sleep

# Prompt_toolkit
from prompt_toolkit.layout.containers import Float, HSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.widgets import Dialog, Label, Button, TextArea
from prompt_toolkit.application.current import get_app
from prompt_toolkit.eventloop import (
    Future,
    ensure_future,
    Return,
    From,
    run_in_executor,
)

# Project
import src.serial_com as serial_com
import src.scenario as scenario
from src.lib import BD_TM, BD_TC
from src.args import args


class TextInputDialog(object):
    def __init__(self, title="", label_text="", completer=None):
        self.future = Future()

        def accept_text(buf):
            get_app().layout.focus(ok_button)
            buf.complete_state = None
            return True

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


def do_upload_hex(ui, upload_type):
    def coroutine():
        open_dialog = TextInputDialog(
            title=f"{upload_type} Upload to SRU",
            label_text="Enter the path of the file:",
            completer=PathCompleter(),
        )

        path = yield From(show_dialog_as_float(open_dialog, ui.root_container))

        if path is not None:
            try:
                with open(path, "rb", buffering=0) as f:
                    data = f.readall()
                    # thread_upload = threading.Thread(
                    #     target=serial_com.upload_hex, args=(ui, data, upload_type)
                    # )
                    # thread_upload.start()
                    # serial_com.upload_hex(ui, data, upload_type)
                    asyncio.ensure_future(serial_com.upload_hex(ui, data, upload_type))

                    # run_in_executor(
                    #     lambda: serial_com.upload_hex(ui, data, upload_type)
                    # )

            except IOError as e:
                show_message("Error", "{}".format(e), ui.root_container)
                get_app().invalidate()

    ensure_future(coroutine())


def do_load_scenario(ui):
    def coroutine():
        open_dialog = TextInputDialog(
            title="Scenario Mode",
            label_text="Enter the path of the file:",
            completer=PathCompleter(),
        )

        path = yield From(show_dialog_as_float(open_dialog, ui.root_container))

        if path is not None:
            open_scenario(ui, path)

    ensure_future(coroutine())


def open_scenario(ui, path, on_startup=False):
    try:
        with open(path, "r") as f:
            scenario_file = f.read()

            scenario_parsed = scenario.parse_scenario(scenario_file)

            if args.check_only:
                show_message(
                    "Scenario Mode", "Scenario's syntax is OK.", ui.root_container
                )
                get_app().invalidate()

            else:
                run_in_executor(
                    lambda: serial_com.play_scenario(ui, scenario_parsed, on_startup),
                    _daemon=True,
                )

    except (ValueError, IOError) as e:

        show_message("Error", "{}".format(e), ui.root_container)

        get_app().invalidate()


def do_conf_TC(current_key, TC_data, ui):
    def coroutine():
        error = False
        param_count = len(BD_TC[ui.TC_selectable_list.current_value]["data"])

        if current_key == param_count:
            serial_com.send_TC(ui.TC_selectable_list.current_value, TC_data, ui)
        else:
            try:
                param_size = int(
                    BD_TC[ui.TC_selectable_list.current_value]["data"][current_key][0]
                )
            except:
                show_message(
                    "Error",
                    f"param count: {param_count}, current key:{current_key}",
                    ui.root_container,
                )

            param_name = BD_TC[ui.TC_selectable_list.current_value]["data"][
                current_key
            ][1]
            param_data = BD_TC[ui.TC_selectable_list.current_value]["data"][
                current_key
            ][2]

            if param_data is not "?":
                TC_data.append(param_data)
            else:
                open_dialog = TextInputDialog(
                    title="TC Parameter",
                    label_text=f"Please enter the hexadecimal value for the parameter: \n{param_name} (length: {param_size} byte(s))",
                )

                result = yield From(
                    show_dialog_as_float(open_dialog, ui.root_container)
                )

                if result is None:
                    error = True
                else:
                    result = result.zfill(2 * param_size).upper()
                    if len(result) > 2 * param_size:
                        error = True
                        show_message(
                            "Error",
                            f"Value too long, {param_size} byte(s) needed.",
                            ui.root_container,
                        )
                        get_app().invalidate()
                    else:
                        try:
                            int(result, 16)
                        except ValueError:
                            error = True
                            show_message(
                                "Error", "Non hexadecimal value.", ui.root_container
                            )
                            get_app().invalidate()
                        else:
                            get_app().invalidate()

                            TC_data.append(result)

            if not error:
                do_conf_TC(current_key + 1, TC_data, ui)

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

        # app.layout.focus(dialog)

    def remove_dialog_as_float(self, root_container):
        if self.float_ in root_container.floats:
            root_container.floats.remove(self.float_)
