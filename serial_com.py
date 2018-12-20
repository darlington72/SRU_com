"""serial_com.py

Handles the serial communication with SRU.
"""

from time import sleep
import threading

# Prompt_toolkit
from prompt_toolkit.application.current import get_app

# Project
import lib
from lib import BD, conf
from args import args
import float_window

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


def look_for_sync_words(ui, ser, first_frame):
    """
    Blocking function that synchronize to the beginning
    of a new frame
    
    Arguments:
        ser -- serial handler

    
    Returns:
        [first_byte, second_byte] -- sync words
    """

    while True:
        first_byte = ser.read(1).hex()
        # ui.buffer_layout.insert_line(f"{first_byte} \n")

        if first_byte in HEADER_DEF[0].keys():
            second_byte = ser.read(1).hex()
            if second_byte in list(
                HEADER_DEF[1][list(HEADER_DEF[0]).index(first_byte)]
            ):
                break
        else:
            if not first_frame:
                ui.buffer_layout.insert_line(
                    "<error>Too many bytes received</error> \n"
                )

    return first_byte, second_byte


def serial_com_TM(ui, ser, lock):
    """Infinite loop that handles bytes received 
    on the serial link
    
    Arguments:
        ui   -- UI instance
        ser  -- Serial instance
        lock -- Thread lock
    """

    first_frame = True
    while True:

        # Looking for sync word
        if first_frame:
            ui.buffer_layout.insert_line(
                "<waiting_sync>Waiting for sync word...</waiting_sync>\n",
                with_time_tag=False,
            )

        sync_word = look_for_sync_words(ui, ser, first_frame)
        first_frame = False

        data_length = int.from_bytes(ser.read(1), "big")

        buffer_feed = "<tm>TM</tm> - "  # Line to be printed to TMTC feed

        # We set the timeout for the frame
        ser.timeout = conf["COM"]["timeout"]

        with lock:

            frame = ser.read(data_length + 2)  # TAG + data + CRC

            if len(frame) < data_length + 2:
                # Timeout occurred

                frame = "".join([format(_, "x").zfill(2) for _ in frame]) + "<error>"
                frame = frame.ljust(((data_length + 2) * 2) + 7, "X")

                buffer_feed += (
                    "<syncword>"
                    + "".join(sync_word)
                    + "</syncword>"
                    + "<datalen>"
                    + format(data_length, "x").zfill(2)
                    + "</datalen>"
                )
                buffer_feed += frame
                buffer_feed += " Timeout error.</error> "

                ui.buffer_layout.insert_line(buffer_feed)
                first_frame = True

            else:
                sync_word_byte = bytearray.fromhex("".join(sync_word))
                frame_byte = sync_word_byte + bytearray([data_length]) + frame
                CRC_calculated = lib.compute_CRC(frame_byte[:-1])
                CRC_received = frame_byte[-1]

                tag, *data, CRC = [format(_, "x").zfill(2).upper() for _ in frame]

                # We set back the timeout to none as next time we'll be looking for syncwords
                ser.timeout = None

                try:
                    frame_name = BD[HEADER_TYPE[sync_word[1]] + "-" + tag]["name"]
                    frame_data = BD[HEADER_TYPE[sync_word[1]] + "-" + tag]["data"]
                except KeyError:
                    frame_name = (
                        "<tan>Frame unrecognized: "
                        + "".join(sync_word)
                        + "-"
                        + tag
                        + "</tan>"
                    )
                    frame_data = False

                if ui.verbose.checked:
                    buffer_feed += lib.format_frame(
                        "<syncword>" + "".join(sync_word) + "</syncword>",
                        "<datalen>" + format(data_length, "x").zfill(2) + "</datalen>",
                        "<tag>" + tag + "</tag>",
                        "<data>" + "".join(data) + "</data>",
                        "<crc>" + CRC + "</crc>",
                        "<b>" + frame_name + "</b>",
                    )
                else:
                    buffer_feed += HEADER_FROM[sync_word[0]] + " - " + frame_name

                if CRC_calculated != CRC_received:
                    buffer_feed += f" <error> Bad CRC: received {CRC}, should be {format(CRC_calculated, 'x').zfill(2)}</error>"

                # Let's print the frame's data if any
                if frame_data:
                    if frame_data[0][0] != "":
                        pointer = 0
                        buffer_feed += " ("
                        for key, value in enumerate(frame_data):
                            if key != 0:
                                buffer_feed += "|"
                            field_length = (
                                int(value[0])
                                if (value[0] != "?")
                                else (
                                    data_length
                                    - sum(
                                        int(data_len[0])
                                        for data_len in frame_data
                                        if data_len[0] != "?"
                                    )
                                )
                            )
                            field_name = value[1]

                            buffer_feed += (
                                field_name
                                + "=<data>0x"
                                + "".join(data[pointer : pointer + field_length]).zfill(
                                    field_length * 2
                                )
                                + "</data>"
                            )
                            pointer = pointer + field_length
                        buffer_feed += ")"

                buffer_feed += "\n"

                ui.buffer_layout.insert_line(buffer_feed)
                lib.write_to_file(
                    "".join(sync_word)
                    + format(data_length, "x").zfill(2)
                    + tag
                    + "".join(data)
                    + CRC
                    + "\n"
                )


def serial_com_watchdog(ui, ser, lock):
    """Infinite loop that sends the watchdog TC every second
    if watchdog_radio is ON
    
    Arguments:
        ui   -- UI instance
        ser  -- Serial instance
        lock -- Thread lock
    """

    while True:

        if ui.watchdog_radio.current_value:
            frame_to_be_sent_str = (
                BD["TC-01"]["header"]
                + BD["TC-01"]["length"]
                + BD["TC-01"]["tag"]
                + "".join([_[2] for _ in BD["TC-01"]["data"]])
            )

            frame_to_be_sent_bytes = bytearray.fromhex(frame_to_be_sent_str)
            CRC = lib.compute_CRC(frame_to_be_sent_bytes)
            frame_to_be_sent_bytes.append(CRC)
            frame_to_be_sent_str += format(CRC, "x").zfill(2)

            with lock:
                ser.write(frame_to_be_sent_bytes)

            lib.write_to_file(frame_to_be_sent_str + "\n")

            # UI
            ui.watchdog_cleared_buffer.text = "      Watchdog Cleared"
            sleep(0.500)
            ui.watchdog_cleared_buffer.text = ""
            sleep(0.500)

        else:
            sleep(1)


def send_TC(TC_data, ui, ser, lock, resend_last_TC=False):
    """Sends a TC over the serial link
    Called by UI instance 
    
    Arguments:
        TC_data {list} -- List of string, each element is a TC parameter 
        ui   -- UI instance
        ser  -- Serial instance
        lock -- Thread lock
    """

    if resend_last_TC:
        if ui.last_TC_sent[0]:
            frame_to_be_sent_bytes = ui.last_TC_sent[0]
            frame_to_be_sent_str = ui.last_TC_sent[1]
            buffer_feed = ui.last_TC_sent[2]



            with lock:
                for key, int_ in enumerate(frame_to_be_sent_bytes):
                    ser.write([int_])
                    if key != len(frame_to_be_sent_bytes) - 1:
                        sleep(conf["COM"]["delay_inter_byte"])

                ui.buffer_layout.insert_line(buffer_feed)
                lib.write_to_file(frame_to_be_sent_str + "\n")

        last_TC_upload_hex = ui.last_TC_sent[3]
        last_TC_hex = ui.last_TC_sent[4]

        if last_TC_upload_hex:
            if last_TC_hex:
                thread_upload = threading.Thread(
                    target=upload_hex, args=(ui, ser, last_TC_hex)
                )
                thread_upload.start()                
            else:
                float_window.do_upload_hex(ui)


    else:
        if "no_TC" not in BD[ui.TC_selectable_list.current_value] or not BD[ui.TC_selectable_list.current_value]["no_TC"]:
            frame_name = BD[ui.TC_selectable_list.current_value]["name"]
            frame_header = BD[ui.TC_selectable_list.current_value]["header"]
            frame_length = BD[ui.TC_selectable_list.current_value]["length"]
            frame_tag = BD[ui.TC_selectable_list.current_value]["tag"]
            frame_data = "".join(TC_data)
            frame_to_be_sent_str = frame_header + frame_length + frame_tag + frame_data
            frame_to_be_sent_bytes = bytearray.fromhex(frame_to_be_sent_str)
            CRC = lib.compute_CRC(frame_to_be_sent_bytes)
            frame_to_be_sent_bytes.append(CRC)
            frame_to_be_sent_str += format(CRC, "x").zfill(2).upper()



            with lock:
                for key, int_ in enumerate(frame_to_be_sent_bytes):
                    ser.write([int_])
                    if key != len(frame_to_be_sent_bytes) - 1:
                        sleep(conf["COM"]["delay_inter_byte"])

                buffer_feed = "<tc>TC</tc> - "  # Line to be printed to TMTC feed

                if ui.verbose.checked:
                    buffer_feed += lib.format_frame(
                        "<syncword>" + frame_header + "</syncword>",
                        "<datalen>" + frame_length + "</datalen>",
                        "<tag>" + frame_tag + "</tag>",
                        "<data>" + frame_data + "</data>",
                        "<crc>" + frame_to_be_sent_str[-2:] + "</crc>",
                        frame_name,
                    )
                else:
                    buffer_feed += frame_name

                buffer_feed += "\n"
                

                ui.buffer_layout.insert_line(buffer_feed)
                lib.write_to_file(frame_to_be_sent_str + "\n")


            # Let's save this TC in case user wants to resend it 
            ui.last_TC_sent[0] = frame_to_be_sent_bytes
            ui.last_TC_sent[1] = frame_to_be_sent_str
            ui.last_TC_sent[2] = buffer_feed
        
        else:
            ui.last_TC_sent[0] = False

        try:
            if BD[ui.TC_selectable_list.current_value]["bootloader"] is True:
                float_window.do_upload_hex(ui)
                ui.last_TC_sent[3] = True
            else:
                ui.last_TC_sent[3] = False
                ui.last_TC_sent[4] = None
        except KeyError:
            ui.last_TC_sent[3] = False
            ui.last_TC_sent[4] = None


def upload_hex(ui, data):
    """Upload a hex file to SRU
    Called by do_upload_hex()
    
    Arguments:
        ui {[type]} -- [description]
        ser {[type]} -- [description]
        data {[type]} -- [description]
    """

    data = data.decode()
    info_message = float_window.InfoDialog(
        "Application Upload to SRU", "Upload in progress..", ui.root_container
    )
    get_app().invalidate()

    # Let's desactivate the watchdog if it's on
    watchdog_value = ui.watchdog_radio.current_value
    if watchdog_value:
        ui.watchdog_radio.set_value(0)

    if args.loop:
        ui.ser.write(bytearray.fromhex("123456A4"))

    data = data.split("\n")

    for line in data:
        if line:
            if line[0] == ":":
                for char in line:
                    ui.ser.write(char.encode())
                    sleep(conf["hex_upload"]["delay_inter_char"])

                sleep(conf["hex_upload"]["delay_inter_line"])

    if args.loop:
        ui.ser.write(bytearray.fromhex("FF"))

    get_app().invalidate()
    info_message.remove_dialog_as_float(ui.root_container)
    get_app().invalidate()
    float_window.show_message(
        "Application Upload to SRU", "Upload done.", ui.root_container
    )

    # Let's turn the watchdog back on
    if watchdog_value:
        ui.watchdog_radio.set_value(1)
