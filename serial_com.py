from time import sleep
import json
import sys
import lib
from prompt_toolkit.application.current import get_app
from lib import BD
import UI
from args import args

# 43 21 Boot TC
# 43 12 Boot TM
# 12 34 App TC
# 12 43 App TM

HEADER_DEF = [
    {"43": "Boot", "12": "App "},
    [{"21": "TC", "12": "TM"}, {"34": "TC", "43": "TM"}],
]
HEADER_FROM = HEADER_DEF[0]
HEADER_TYPE = {**HEADER_DEF[1][0], **HEADER_DEF[1][1]}


def write_to_file(line):
    if args.file is not None:
        with open(args.file + ".txt", mode="a") as file:
            file.write(line)


def serial_com_TM(ser, lock, buffer_layout, TM_window, loop_mode=False):

    # with lock:
    buffer_layout.text = "Waiting for sync word..."

    if loop_mode:
        sleep(
            0.5
        )  # In loop mode, we give a chance to serial_com_TC to send out one frame before looking for sync word.

    while True:
        first_byte = ser.read(1).hex()
        if first_byte in HEADER_DEF[0].keys():
            second_byte = ser.read(1).hex()
            if second_byte in list(
                HEADER_DEF[1][list(HEADER_DEF[0]).index(first_byte)]
            ):
                break
        sleep(0.1)  # To be able to catch exit call

    buffer_layout.text += "found ! \n"
    buffer_layout._set_cursor_position(len(buffer_layout.text))

    # first_frame_data_lenght = int.from_bytes(ser.read(1), "big")
    # ser.read(
    #     first_frame_data_lenght + 2
    # )  # Let's read the first frame entirely, then we are properly synced

    first_frame = True
    sync_word = [first_byte, second_byte]
    data_lenght = int.from_bytes(ser.read(1), "big")

    while True:
        buffer_feed = "<tm>TM</tm> - "  # Line to be printed to TMTC feed

        # FIXME: read(1) call, and when it succeeds use read(inWaiting())

        if first_frame:
            first_frame = False
        else:
            *sync_word, data_lenght = ser.read(3)
            # when using unpacking, ser.read return are cast to int

            sync_word = [format(_, "x") for _ in sync_word]
            # "HEX"

        tag, *data, CRC = [format(_, "x") for _ in ser.read(data_lenght + 2)]

        tag = str(tag) if len(str(tag)) > 1 else "0" + str(tag)
        try:
            frame_name = BD[HEADER_TYPE[sync_word[1]] + "-" + tag]["name"]
            frame_data = BD[HEADER_TYPE[sync_word[1]] + "-" + tag]["data"]
        except KeyError:
            frame_name = (
                "<tan>Frame unrecognized: " + "".join(sync_word) + "-" + tag + "</tan>"
            )
            frame_data = False

        if UI.verbose.checked:
            buffer_feed += lib.format_frame(
                "<syncword>" + "".join(sync_word) + "</syncword>",
                "<datalen>" + format(data_lenght, "x").zfill(2) + "</datalen>",
                "<tag>" + tag.zfill(2) + "</tag>",
                "<data>" + "".join(data) + "</data>",
                "<crc>" + CRC.zfill(2) + "</crc>",
                "<b>" + frame_name + "</b>",
            )
        else:
            buffer_feed += HEADER_FROM[sync_word[0]] + " - " + frame_name

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
                    + "=<data>0x"
                    + "".join(data[pointer : pointer + field_lenght]).zfill(2)
                    + "</data>"
                )
                pointer = pointer + field_lenght
            buffer_feed += ")"

        buffer_feed += "\n"

        buffer_layout.insert_line(buffer_feed)
        write_to_file(
            "".join(sync_word)
            + format(data_lenght, "x")
            + tag
            + "".join(data)
            + CRC
            + "\n"
        )

        if not get_app().layout.has_focus(TM_window):
            buffer_layout._set_cursor_position(len(buffer_layout.text) - 1)

        sleep(0.01)


def serial_com_watchdog(
    ser, lock, buffer_layout, TM_window, watchdog_radio, loop_mode=False
):
    if loop_mode:
        frame_to_be_sent = (
            BD["TC-01"]["header"]
            + BD["TC-01"]["length"]
            + BD["TC-01"]["tag"]
            + "".join([_[2] for _ in BD["TC-01"]["data"]])
            + BD["TC-01"]["CRC"]
        )
        ser.write(bytearray.fromhex(frame_to_be_sent))

    while True:
        # buffer_feed = "TC - "  # Line to be printed to TMTC feed

        if watchdog_radio.current_value:
            frame_to_be_sent = (
                BD["TC-01"]["header"]
                + BD["TC-01"]["length"]
                + BD["TC-01"]["tag"]
                + "".join([_[2] for _ in BD["TC-01"]["data"]])
                + BD["TC-01"]["CRC"]
            )

            with lock:
                ser.write(bytearray.fromhex(frame_to_be_sent))

            UI.watchdog_cleared_buffer.text = "      Watchdog Cleared"
            sleep(1)
            UI.watchdog_cleared_buffer.text = ""
            sleep(1)

        else:
            sleep(1)


def send_TC(ser, lock, buffer_layout, TC_list, TM_window):
    frame_to_be_sent = (
        BD[TC_list.current_value]["header"]
        + BD[TC_list.current_value]["length"]
        + BD[TC_list.current_value]["tag"]
        + "".join([_[2] for _ in BD[TC_list.current_value]["data"]])
        + BD[TC_list.current_value]["CRC"]
    )

    with lock:
        ser.write(bytearray.fromhex(frame_to_be_sent))

        buffer_feed = "<tc>TC</tc> - "  # Line to be printed to TMTC feed

        if UI.verbose.checked:
            buffer_feed += lib.format_frame(
                "<syncword>" + BD[TC_list.current_value]["header"] + "</syncword>",
                "<datalen>" + BD[TC_list.current_value]["length"] + "</datalen>",
                "<tag>" + BD[TC_list.current_value]["tag"] + "</tag>",
                "<data>"
                + "".join([_[2] for _ in BD[TC_list.current_value]["data"]])
                + "</data>",
                "<crc>" + BD[TC_list.current_value]["CRC"] + "</crc>",
                BD[TC_list.current_value]["name"],
            )
        else:
            buffer_feed += BD[TC_list.current_value]["name"]

        buffer_feed += "\n"

        buffer_layout.insert_line(buffer_feed)
        write_to_file(frame_to_be_sent + "\n")
        if not get_app().layout.has_focus(TM_window):
            buffer_layout._set_cursor_position(len(buffer_layout.text) - 1)

