from time import sleep
import json
import sys
import lib
from prompt_toolkit.application.current import get_app
from lib import BD
import UI


def serial_com_TM(ser, lock, buffer_layout, TM_window, loop_mode=False):

    with lock:
        buffer_layout.text = "Waiting for sync word..."

        if loop_mode:
            sleep(
                0.5
            )  # In loop mode, we give a chance to serial_com_TC to send out one frame before looking for sync word.

        while True:
            first_byte = ser.read(1).hex()
            if first_byte in ("12", "43"):
                second_byte = ser.read(1).hex()
                if (first_byte == "12" and (second_byte == "34" or second_byte="43")) or (
                    first_byte == "43" and (second_byte == "21" or second_byte="12")
                ):
                    break

        buffer_layout.text += "found ! \n"
        buffer_layout._set_cursor_position(len(buffer_layout.text))

        first_frame_data_lenght = int.from_bytes(ser.read(1), "big")
        ser.read(
            first_frame_data_lenght + 2
        )  # Let's read the first frame entirely, then we are properly synced

    while True:
        buffer_feed = ""  # Line to be printed to TMTC feed

        # FIXME read(1) call, and when it succeeds use read(inWaiting())
        *sync_word, data_lenght = ser.read(3)
        # for no reason ser.read returns int here..
        sync_word = [format(_, "x") for _ in sync_word]

        tag, *data, CRC = [format(_, "x") for _ in ser.read(data_lenght + 2)]

        tag = str(tag) if len(str(tag)) > 1 else str(tag) + "0"
        try:
            frame_name = BD[tag]["name"]
            frame_data = BD[tag]["data"]
        except KeyError:
            frame_name = "<tan>Frame unrecognized</tan>"
            frame_data = False

        if UI.verbose.checked:
            buffer_feed += lib.format_frame(
                "".join(sync_word),
                format(data_lenght, "x"),
                tag,
                "".join(data),
                CRC,
                "<b>" + frame_name + "</b>",
            )
        else:
            buffer_feed += frame_name

        if frame_data:
            pointer = 0
            buffer_feed += " ("
            for key, value in enumerate(frame_data):
                if key != 0:
                    buffer_feed += "|"
                field_lenght = int(value[0])
                field_name = value[1]

                buffer_feed += (
                    field_name
                    + "=<skyblue>0x"
                    + "".join(data[pointer : pointer + field_lenght])
                    + "</skyblue>"
                )
                pointer = pointer + field_lenght
            buffer_feed += ")"

        buffer_feed += "\n"

        buffer_layout.insert_line(buffer_feed)

        if not get_app().layout.has_focus(TM_window):
            buffer_layout._set_cursor_position(len(buffer_layout.text) - 1)

        sleep(0.01)


def serial_com_TC(ser, lock, buffer_layout, watchdog_radio, loop_mode=False):
    if loop_mode:
        frame_to_be_sent = (
            BD["01"]["header"]
            + BD["01"]["length"]
            + BD["01"]["tag"]
            + BD["01"]["data"]
            + BD["01"]["CRC"]
        )
        ser.write(bytearray.fromhex(frame_to_be_sent))

    while True:
        buffer_feed = ""  # Line to be printed to TMTC feed

        if watchdog_radio.current_value:
            frame_to_be_sent = (
                BD["01"]["header"]
                + BD["01"]["length"]
                + BD["01"]["tag"]
                + BD["01"]["data"]
                + BD["01"]["CRC"]
            )

            with lock:
                ser.write(bytearray.fromhex(frame_to_be_sent))
                if UI.verbose.checked:
                    buffer_feed += lib.format_frame(
                        BD["01"]["header"],
                        BD["01"]["length"],
                        BD["01"]["tag"],
                        BD["01"]["data"],
                        BD["01"]["CRC"],
                        BD["01"]["name"],
                    )
                else:
                    buffer_feed += BD["01"]["name"]

                buffer_feed += "\n"
                buffer_layout.insert_line(buffer_feed)

        sleep(1)


def send_TC(ser, lock, buffer_layout, TC_list, TM_window):
    frame_to_be_sent = (
        BD[TC_list.current_value]["header"]
        + BD[TC_list.current_value]["length"]
        + BD[TC_list.current_value]["tag"]
        + BD[TC_list.current_value]["data"]
        + BD[TC_list.current_value]["CRC"]
    )

    with lock:
        ser.write(bytearray.fromhex(frame_to_be_sent))

        buffer_feed = ""  # Line to be printed to TMTC feed


        if UI.verbose.checked:
            buffer_feed += lib.format_frame(
                BD[TC_list.current_value]["header"],
                BD[TC_list.current_value]["length"],
                BD[TC_list.current_value]["tag"],
                BD[TC_list.current_value]["data"],
                BD[TC_list.current_value]["CRC"],
                BD[TC_list.current_value]["name"],
            )
        else:
            buffer_feed += BD[TC_list.current_value]["name"]

        buffer_feed += "\n"

        buffer_layout.insert_line(buffer_feed)

        if not get_app().layout.has_focus(TM_window):
            buffer_layout._set_cursor_position(len(buffer_layout.text) - 1)

