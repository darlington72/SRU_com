"""serial_com.py

Handles the serial communication with SRU.
"""

from time import sleep
import threading
import asyncio
from queue import Empty
import queue

# Prompt_toolkit
from prompt_toolkit.application.current import get_app
from prompt_toolkit import HTML
from prompt_toolkit.eventloop import Future, ensure_future, Return, From

# Project
import src.lib as lib
from src.lib import BD_TC, BD_TM, conf
from src.args import args
import src.float_window as float_window


# To debug:
# ui.buffer_layout.insert_line("STWAP \n")

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


def look_for_sync_words(ui, first_frame):
    """
    Blocking function that synchronize to the beginning
    of a new frame
    
    Arguments:
        ser -- serial handler

    
    Returns:
        [first_byte, second_byte] -- sync words
    """

    while True:
        first_byte = ui.ser.read(1).hex()
        # ui.buffer_layout.insert_line(f"{first_byte} \n")

        if first_byte in HEADER_DEF[0].keys():
            # We set the timeout for the frame
            ui.ser.timeout = conf["COM"]["timeout"]

            second_byte = ui.ser.read(1).hex()

            if len(str(second_byte)) < 1:
                # Timeout occured after syncword reception
                buffer_feed = "<tm>TM</tm> - "  # Line to be printed to TMTC feed
                buffer_feed += (
                    "<syncword>"
                    + "".join(first_byte)
                    + "</syncword><error> Timeout error</error> \n"
                )
                ui.buffer_layout.insert_line(buffer_feed)
                first_frame = True
            else:
                if second_byte in list(
                    HEADER_DEF[1][list(HEADER_DEF[0]).index(first_byte)]
                ):
                    break
        else:
            if not first_frame:
                ui.buffer_layout.insert_line(
                    "".join(first_byte) + " <error>Too many bytes received</error> \n"
                )

    return first_byte, second_byte


def serial_com_TM(ui):
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

        sync_word = look_for_sync_words(ui, first_frame)
        first_frame = False

        data_length = int.from_bytes(ui.ser.read(1), "big")
        # ui.buffer_layout.insert_line(f"DATA LENGTH ={data_length}")

        buffer_feed = "<tm>TM</tm> - "  # Line to be printed to TMTC feed

        if len(str(data_length)) < 1:
            # Timeout occured after syncword reception
            buffer_feed += (
                "<syncword>"
                + "".join(sync_word)
                + "</syncword><error> Timeout error</error>"
            )
            ui.buffer_layout.insert_line(buffer_feed)
            first_frame = True

        else:
            with ui.lock:
                frame = ui.ser.read(data_length + 2)  # TAG + data + CRC
                if len(frame) < data_length + 2:
                    # Timeout occurred

                    frame = (
                        "".join([format(_, "x").zfill(2) for _ in frame]) + "<error>"
                    )
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
                    ui.ser.timeout = None

                    try:
                        frame_name = BD_TM[HEADER_TYPE[sync_word[1]] + "-" + tag][
                            "name"
                        ]
                        frame_data = BD_TM[HEADER_TYPE[sync_word[1]] + "-" + tag][
                            "data"
                        ]
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
                            "<datalen>"
                            + format(data_length, "x").zfill(2)
                            + "</datalen>",
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
                            for key, value in enumerate(frame_data):
                                buffer_feed += "\n" + " " * 18

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
                                    + " "
                                    + " "
                                    * (
                                        len(
                                            max(
                                                [data[1] for data in frame_data],
                                                key=len,
                                            )
                                        )
                                        - (len(field_name))
                                    )
                                    + "= <data>0x"
                                    + "".join(
                                        data[pointer : pointer + field_length]
                                    ).zfill(field_length * 2)
                                    + "</data>"
                                )
                                pointer = pointer + field_length
                            # buffer_feed += ")"

                    buffer_feed += "\n"

                    ui.buffer_layout.insert_line(buffer_feed)
                    lib.write_to_file(
                        ui.file_,
                        "".join(sync_word)
                        + format(data_length, "x").zfill(2)
                        + tag
                        + "".join(data)
                        + CRC
                        + "\n",
                    )
                    # if last tm was not read, we clear it
                    if not ui.last_TM.full():
                        ui.last_TM.put({"tag": tag, "data": data})


def serial_com_watchdog(ui):
    """Infinite loop that sends the watchdog TC every second
    if watchdog_radio is ON
    
    Arguments:
        ui   -- UI instance
        ser  -- Serial instance
        lock -- Thread lock
    """

    watchdog_TC_tag = conf["TC_watchdog_tag"]

    while True:

        if ui.watchdog_radio.current_value:
            frame_to_be_sent_str = (
                BD_TC["TC-" + watchdog_TC_tag]["header"]
                + BD_TC["TC-" + watchdog_TC_tag]["length"]
                + BD_TC["TC-" + watchdog_TC_tag]["tag"]
            )

            frame_to_be_sent_bytes = bytearray.fromhex(frame_to_be_sent_str)
            CRC = lib.compute_CRC(frame_to_be_sent_bytes)
            frame_to_be_sent_bytes.append(CRC)
            frame_to_be_sent_str += format(CRC, "x").zfill(2)

            with ui.lock:
                ui.ser.write(frame_to_be_sent_bytes)

            lib.write_to_file(ui.file_, frame_to_be_sent_str + "\n")

            # UI
            ui.watchdog_cleared_buffer.text = "      Watchdog Cleared"
            sleep(0.500)
            ui.watchdog_cleared_buffer.text = ""
            sleep(0.500)

        else:
            sleep(1)


def send_TC(TC_id, TC_data, ui, resend_last_TC=False):
    """Sends a TC over the serial link
    Called by UI instance or hex_upload
    
    Arguments:
        TC_data {list} -- List of string, each element is a TC parameter 
        ui   -- UI instance
        ser  -- Serial instance
        lock -- Thread lock
        resend_last_TC -- 
    """

    if resend_last_TC:
        if ui.last_TC_sent["frame_bytes"]:
            frame_to_be_sent_bytes = ui.last_TC_sent["frame_bytes"]
            frame_to_be_sent_str = ui.last_TC_sent["frame_str"]
            buffer_feed = ui.last_TC_sent["buffer_feed"]

            with ui.lock:
                for key, int_ in enumerate(frame_to_be_sent_bytes):
                    ui.ser.write([int_])
                    if key != len(frame_to_be_sent_bytes) - 1:
                        sleep(conf["COM"]["delay_inter_byte"])

                ui.buffer_layout.insert_line(buffer_feed)
                lib.write_to_file(ui.file_, frame_to_be_sent_str + "\n")

        last_TC_upload_hex = ui.last_TC_sent["hex_upload"]
        last_TC_hex = ui.last_TC_sent["hex_file"]

        if last_TC_upload_hex:
            if last_TC_hex:
                asyncio.ensure_future(upload_hex(ui, last_TC_hex))

            # else:
            #     float_window.do_upload_hex(ui)

    else:
        frame_name = BD_TC[TC_id]["name"]
        frame_header = BD_TC[TC_id]["header"]
        frame_tag = BD_TC[TC_id]["tag"]
        frame_data = "".join(TC_data)
        frame_length = hex(int(len(frame_data) / 2))[2:].zfill(2)
        frame_to_be_sent_str = frame_header + frame_length + frame_tag + frame_data
        frame_to_be_sent_bytes = bytearray.fromhex(frame_to_be_sent_str)
        CRC = lib.compute_CRC(frame_to_be_sent_bytes)
        frame_to_be_sent_bytes.append(CRC)
        frame_to_be_sent_str += format(CRC, "x").zfill(2).upper()

        with ui.lock:
            for key, int_ in enumerate(frame_to_be_sent_bytes):
                ui.ser.write([int_])
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
        # ui.raw_serial_buffer.text += HTML("<TC>" + buffer_feed[:-1] + "</TC>")
        lib.write_to_file(ui.file_, frame_to_be_sent_str + "\n")

        # Let's save this TC in case user wants to resend it
        ui.last_TC_sent["frame_bytes"] = frame_to_be_sent_bytes
        ui.last_TC_sent["frame_str"] = frame_to_be_sent_str
        ui.last_TC_sent["buffer_feed"] = buffer_feed
        ui.last_TC_sent["hex_upload"] = False

        # try:
        #     if BD_TC[TC_id]["bootloader"] is True:
        #         float_window.do_upload_hex(ui)
        #         ui.last_TC_sent["hex_upload"] = True
        #     else:
        #         ui.last_TC_sent["hex_upload"] = False
        #         ui.last_TC_sent["hex_file"] = None
        # except KeyError:
        #     ui.last_TC_sent["hex_upload"] = False
        #     ui.last_TC_sent["hex_file"] = None


async def upload_hex(ui, data, upload_type=None):
    """Upload a hex file to SRU
    Called by do_upload_hex()
    
    Arguments:
        ui {[type]} -- [description]
        ser {[type]} -- [description]
        data {[type]} -- [description]
    """

    error = False

    if upload_type == None:
        # if upload_hex was called by <ctrl> + R
        upload_type = ui.last_TC_sent["upload_type"]
    else:
        # if not, we save it for next <ctrl> + R
        ui.last_TC_sent["upload_type"] = upload_type

    # Let's keep a backup of data for last TC resend shortcut
    data_backup = data

    data = data.decode()
    info_message = float_window.InfoDialog(
        f"{upload_type} Upload to SRU", "Erase in progress.. (1/3)", ui.root_container
    )
    get_app().invalidate()

    # Let's desactivate the watchdog if it's on
    watchdog_value = ui.watchdog_radio.current_value
    if watchdog_value:
        ui.watchdog_radio.set_value(0)

    # Erasing memory before upload

    if upload_type == "Golden":
        # let's send the TC erase MRAM golden
        ui.buffer_layout.insert_line('Sending TC "(BL) Erase Golden in MRAM"\n')
        send_TC(
            "TC-" + conf["hex_upload"]["TC_erase_MRAM_GOLDEN_tag"],
            [],
            ui,
            resend_last_TC=False,
        )

    elif upload_type == "Application":
        # let's send the TC erase MRAM app
        ui.buffer_layout.insert_line('Sending TC "Erase Appli in MRAM"\n')
        send_TC(
            "TC-" + conf["hex_upload"]["TC_erase_MRAM_APP_tag"],
            [],
            ui,
            resend_last_TC=False,
        )
    else:
        raise TypeError

    # let's wait for TM MRAM erased
    ui.clear_last_TM_buffer()

    await asyncio.sleep(0.005)  # async sleep to refresh UI

    TM_received = ui.wait_for_TM(timeout=conf["hex_upload"]["max_wait_erase_app"])
    if not TM_received:
        ui.buffer_layout.insert_line(
            "<error>Error: TM MRAM erased not received</error>\n"
        )
        error = True
    else:
        if upload_type == "Application":
            if TM_received["tag"] != conf["hex_upload"]["TM_MRAM_APP_erased_tag"]:
                ui.buffer_layout.insert_line(
                    "<error>Error: Was expecting TM MRAM erased</error>\n"
                )
                if not ui.ser.test:
                    error = True

        else:
            if TM_received["tag"] != conf["hex_upload"]["TM_MRAM_GOLDEN_erased_tag"]:
                ui.buffer_layout.insert_line(
                    "<error>Error: Was expecting TM MRAM erased</error>\n"
                )
                if not ui.ser.test:
                    error = True

    get_app().invalidate()
    info_message.remove_dialog_as_float(ui.root_container)

    if not error:

        info_message = float_window.InfoDialog(
            f"{upload_type} Upload to SRU",
            "Upload in progress.. (2/3) \n(can take up to 30s)",
            ui.root_container,
        )
        get_app().invalidate()

        await asyncio.sleep(0.005)
        data = data.split("\n")

        for line in data:
            if line:
                if line[0] == ":":
                    line = line.strip()
                    if upload_type == "Golden":
                        send_TC(
                            "TC-"
                            + conf["hex_upload"]["TC_GOLDEN_hex_line_upload_tag"]
                            + "(BL)",
                            [line[1:]],
                            ui,
                            resend_last_TC=False,
                        )
                    elif upload_type == "Application":
                        send_TC(
                            "TC-" + conf["hex_upload"]["TC_APP_hex_line_upload_tag"],
                            [line[1:]],
                            ui,
                            resend_last_TC=False,
                        )
                    else:
                        raise TypeError

                    if conf["hex_upload"]["refresh_ui_during_upload"]:
                        await asyncio.sleep(conf["hex_upload"]["delay_inter_line"])
                    else:
                        sleep(conf["hex_upload"]["delay_inter_line"])

        # CRC calculation
        CRC_calculated = lib.compute_CRC_hex(data, ui).zfill(2)
        ui.buffer_layout.insert_line(
            f"CRC calulated = 0x{CRC_calculated}. Sending CRC frame to SRU..\n"
        )

        info_message.remove_dialog_as_float(ui.root_container)
        info_message = float_window.InfoDialog(
            f"{upload_type} Upload to SRU",
            "Waiting for SRU CRC calculation.. (3/3)",
            ui.root_container,
        )
        get_app().invalidate()
        await asyncio.sleep(0.005)  # async sleep to refresh UI

        # Let's send calculated CRC
        ui.clear_last_TM_buffer()

        if upload_type == "Application":

            send_TC(
                "TC-" + conf["hex_upload"]["TC_CRC_APP_tag"],
                [CRC_calculated],
                ui,
                resend_last_TC=False,
            )
        else:
            send_TC(
                "TC-" + conf["hex_upload"]["TC_CRC_GOLDEN_tag"],
                [CRC_calculated],
                ui,
                resend_last_TC=False,
            )

        await asyncio.sleep(0.005)  # async sleep to refresh UI

        # Wait for answer
        CRC_received = ui.wait_for_TM(
            timeout=conf["hex_upload"]["max_wait_CRC_calculation"]
        )

        if not CRC_received:
            error = True
            ui.buffer_layout.insert_line(
                "<error>Error:</error> CRC frame from SRU not received.\n"
            )
        else:
            await asyncio.sleep(0.005)  # async sleep to refresh UI
            try:
                if not ui.ser.test and CRC_received["data"][1] != CRC_calculated:
                    error = True
                    ui.buffer_layout.insert_line(
                        f"<error>CRC ERROR: received 0x{CRC_received['data'][1]}, calculated 0x{CRC_calculated}</error>\n"
                    )
                else:
                    if upload_type == "Application":
                        if conf["hex_upload"]["send_TC_reboot_after_app_upload"]:

                            # Clearing the last_TM buffer
                            ui.clear_last_TM_buffer()

                            # Sending the TC Request Reload Appli
                            ui.buffer_layout.insert_line(
                                'Sending TC "Request Reload Appli from MRAM"\n'
                            )
                            send_TC(
                                "TC-" + conf["hex_upload"]["TC_reload_APP_tag"],
                                [],
                                ui,
                                resend_last_TC=False,
                            )

                            await asyncio.sleep(0.005)  # async sleep to refresh UI

                            # Waiting for TM Reload Appli
                            TM_received = ui.wait_for_TM(
                                timeout=conf["hex_upload"]["max_wait_CRC_calculation"]
                            )

                            if not TM_received:
                                ui.buffer_layout.insert_line(
                                    "<error>Error:</error> TM reloaded APP not received.\n"
                                )
                            else:
                                if (
                                    TM_received["tag"]
                                    != conf["hex_upload"]["TM_reload_APP_tag"]
                                ):
                                    if not ui.ser.test:
                                        error = True
                                    ui.buffer_layout.insert_line(
                                        "<error>Error:</error> Was expecting TM reloaded APP.\n"
                                    )
                                else:
                                    ui.buffer_layout.insert_line(
                                        'Sending TC "Reboot"\n'
                                    )
                                    send_TC(
                                        "TC-" + conf["hex_upload"]["TC_reboot_tag"],
                                        [],
                                        ui,
                                        resend_last_TC=False,
                                    )
                    else:
                        if conf["hex_upload"]["send_TC_reboot_after_golden_upload"]:
                            ui.buffer_layout.insert_line('Sending TC "Reboot"\n')
                            send_TC(
                                "TC-" + conf["hex_upload"]["TC_reboot_tag"] + "(BL)",
                                [],
                                ui,
                                resend_last_TC=False,
                            )
                    await asyncio.sleep(0.005)  # async sleep to refresh UI
            except IndexError:
                ui.buffer_layout.insert_line(
                    "<error>Error:</error> CRC frame from SRU is not correct.\n"
                )

        info_message.remove_dialog_as_float(ui.root_container)
        get_app().invalidate()

        if not error:
            float_window.show_message(
                f"{upload_type} Upload to SRU", "Upload done.", ui.root_container
            )

        ui.last_TC_sent["hex_upload"] = True
        ui.last_TC_sent["hex_file"] = data_backup
        ui.last_TC_sent["frame_bytes"] = False

        # Let's turn the watchdog back on
        if watchdog_value:
            ui.watchdog_radio.set_value(1)
