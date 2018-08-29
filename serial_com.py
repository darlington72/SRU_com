from time import sleep, time
import sys
import lib
from prompt_toolkit.application.current import get_app
from prompt_toolkit.shortcuts import message_dialog
from lib import BD, conf
import UI
from args import args
import bootloader_window

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


def look_for_sync_words(ser, first_frame):
    """
    Blocking function that synchronise to the beginning
    of a new frame
    
    Arguments:
        ser -- serial handler

    
    Returns:
        [first_byte, second_byte] -- sync words
    """

    while True:
        first_byte = ser.read(1).hex()
        if first_byte in HEADER_DEF[0].keys():
            second_byte = ser.read(1).hex()
            if second_byte in list(
                HEADER_DEF[1][list(HEADER_DEF[0]).index(first_byte)]
            ):
                break
        else:
            if not first_frame:
                UI.buffer_layout.insert_line('<error>Too many bytes received</error> \n')
        
        # sleep(0.10)

    return first_byte, second_byte


# FIXME: Move to lib.py
def write_to_file(line):
    if args.file is not None:
        with open(args.file + ".txt", mode="a") as file:
            file.write(line)


def serial_com_TM(ser, lock):

    first_frame = True
    while True:

        # Looking for sync word

        if first_frame:
            UI.buffer_layout.insert_line(
                "<waiting_sync>Waiting for sync word...</waiting_sync>\n",
                with_time_tag=False,
            )
            if not get_app().layout.has_focus(UI.TM_window):
                UI.buffer_layout._set_cursor_position(len(UI.buffer_layout.text) - 1)
            
    
        sync_word = look_for_sync_words(ser, first_frame)
        first_frame = False

        data_length = int.from_bytes(ser.read(1), "big")

        buffer_feed = "<tm>TM</tm> - "  # Line to be printed to TMTC feed

        # FIXME: read(1) call, and when it succeeds use read(inWaiting())

        # We set the timeout for the frame 
        ser.timeout = conf['COM']['timeout'] 

        frame = ser.read(data_length + 2)

        if len(frame) < data_length + 2:
            # Timeout occurred

            frame = "".join([format(_, "x") for _ in frame]) + "<error>"
            frame = frame.ljust(((data_length + 2) * 2) + 7, "X")

            buffer_feed += "<syncword>" + "".join(sync_word) + "</syncword>" +  "<datalen>" + format(data_length, "x").zfill(2) + "</datalen>"
            buffer_feed += frame
            buffer_feed += ' Timeout error.</error> '

            UI.buffer_layout.insert_line(buffer_feed)
            first_frame = True 
            
        else:
            tag, *data, CRC = [format(_, "x") for _ in frame]

            # We set back the timeout to none as next time we'll be looking for syncword
            ser.timeout = None

            tag = tag.zfill(2).upper()

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
                    "<datalen>" + format(data_length, "x").zfill(2) + "</datalen>",
                    "<tag>" + tag.zfill(2) + "</tag>",
                    "<data>" + "".join(data) + "</data>",
                    "<crc>" + CRC.zfill(2) + "</crc>",
                    "<b>" + frame_name + "</b>",
                )
            else:
                buffer_feed += HEADER_FROM[sync_word[0]] + " - " + frame_name

            # Let's print the frame's data if any
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
                        + "".join(data[pointer : pointer + field_lenght]).zfill(
                            field_lenght * 2
                        )
                        + "</data>"
                    )
                    pointer = pointer + field_lenght
                buffer_feed += ")"

            buffer_feed += "\n"

            UI.buffer_layout.insert_line(buffer_feed)
            write_to_file(
                "".join(sync_word)
                + format(data_length, "x")
                + tag
                + "".join(data)
                + CRC
                + "\n"
            )

            if not get_app().layout.has_focus(UI.TM_window):
                UI.buffer_layout._set_cursor_position(len(UI.buffer_layout.text) - 1)

        # sleep(0.5)


def serial_com_watchdog(ser, lock):

    while True:
        # buffer_feed = "TC - "  # Line to be printed to TMTC feed

        if UI.watchdog_radio.current_value:
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
            sleep(0.500)
            UI.watchdog_cleared_buffer.text = ""
            sleep(0.500)

        else:
            sleep(1)


def send_TC(ser, lock, TC_list, root_container):
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

        UI.buffer_layout.insert_line(buffer_feed)
        write_to_file(frame_to_be_sent + "\n")
        if not get_app().layout.has_focus(UI.TM_window):
            UI.buffer_layout._set_cursor_position(len(UI.buffer_layout.text) - 1)

    if BD[TC_list.current_value]["name"] == "bootloader":
        bootloader_window.do_open_file(ser, root_container)


def upload_app(ser, data, root_container):
    data = data.decode()
    # info_message = bootloader_window.InfoDialog("Upload in progress..", "test", root_container)

    # sleep(5)
    # info_message.remove_dialog_as_float(root_container)
    # info_message2 = bootloader_window.InfoDialog("Upload in progress..", "test 2", root_container)
    # info_message = bootloader_window.InfoDialog("Upload in progress..", data, root_container)
    # bootloader_window.show_message('Upload', data, root_container, button=True)

    # with lock:

    # Let's desactivate the watchdog if it's on
    watchdog_value = UI.watchdog_radio.current_value
    if watchdog_value:
        UI.watchdog_radio.set_value(0)

    if args.loop:
        ser.write(bytearray.fromhex("123456A4"))

    data = data.split("\n")

    for line in data:
        if line:
            if line[0] == ":":
                for char in line:
                    ser.write(char.encode())
                    sleep(conf["hex_upload"]["delay_inter_char"])

                sleep(conf["hex_upload"]["delay_inter_line"])

    if args.loop:
        ser.write(bytearray.fromhex("FF"))

    bootloader_window.show_message(
        "Application Upload to SRU", "Upload done.", root_container
    )

    # Let's turn the watchdog back on
    if watchdog_value:
        UI.watchdog_radio.set_value(1)
