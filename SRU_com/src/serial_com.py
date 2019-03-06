"""serial_com.py

Handles the communication with SRU.
"""

from time import sleep
import threading
import asyncio
from queue import Empty
import queue
import datetime
import sys

# Prompt_toolkit
from prompt_toolkit.application.current import get_app
from prompt_toolkit import HTML
from prompt_toolkit.eventloop import (
    Future,
    ensure_future,
    Return,
    From,
    call_from_executor,
)

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
        ui -- UI instance
        first_frame {bool} -- Whether it is the first frame or not 

    
    Returns:
        [first_byte, second_byte] -- sync words
    """

    while True:
        first_byte = ui.ser.read(1).hex()
        # ui.buffer_layout.insert_line(f"Premier {first_byte}")

        if first_byte in HEADER_DEF[0].keys():
            # ui.buffer_layout.insert_line(f"En attente second")

            # We set the timeout for the frame
            ui.ser.timeout = conf["COM"]["timeout"]

            second_byte = ui.ser.read(1).hex()
            # ui.buffer_layout.insert_line(f"Second {second_byte}")

            if len(str(second_byte)) < 1:
                # Timeout occured after syncword reception
                buffer_feed = "<tm>TM</tm> - "  # Line to be printed to TMTC feed
                buffer_feed += (
                    "<syncword>"
                    + "".join(first_byte)
                    + "</syncword><error> Timeout error</error>"
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
                    "".join(first_byte) + " <error>Too many bytes received</error>"
                )

    return first_byte, second_byte


def serial_com_TM(ui):
    """Infinite loop that handles bytes received 
    on the serial link
    
    Arguments:
        ui   -- UI instance
    """

    first_frame = True

    while True:

        # Looking for sync word
        if first_frame:
            ui.buffer_layout.insert_line(
                "<waiting_sync>Waiting for sync word...</waiting_sync>",
                with_time_tag=False
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

                    ui.buffer_layout.insert_line(buffer_feed)
                    # call_from_executor(lambda: ui.buffer_layout.insert_line(buffer_feed))

                    # if last tm was not read, we clear it
                    if not ui.last_TM.full():
                        ui.last_TM.put({"tag": tag, "data": data})


def serial_com_watchdog(ui):
    """Infinite loop that sends the watchdog TC every second
    if watchdog_radio is ON
    
    Arguments:
        ui   -- UI instance
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
            frame_to_be_sent_str += format(CRC, "x").zfill(2).upper()

            with ui.lock:
                ui.ser.write(frame_to_be_sent_bytes)

            # Blinking text in the UI 
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
        resend_last_TC -- True if send_TC was called by <ctrl> + R
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
            if conf["COM"]["delay_inter_byte"] == 0 or args.socket:
                ui.ser.write(frame_to_be_sent_bytes)
            else:
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

        ui.buffer_layout.insert_line(buffer_feed)
        # call_from_executor(lambda: ui.buffer_layout.insert_line(buffer_feed))

        # Let's save this TC in case user wants to resend it
        ui.last_TC_sent["frame_bytes"] = frame_to_be_sent_bytes
        ui.last_TC_sent["frame_str"] = frame_to_be_sent_str
        ui.last_TC_sent["buffer_feed"] = buffer_feed
        ui.last_TC_sent["hex_upload"] = False
        ui.last_TC_sent["bytes_only"] = False


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


async def upload_hex(ui, data, upload_type=None, from_scenario=False):
    """Upload a hex file to SRU
    Called by do_upload_hex()
    
    Arguments:
        ui  -- UI instance
        data {str} -- Data to be upload 
        upload_type {"Golden" || "Application"} -- Whether it is a golden or app upload
    """

    error = False
    ui.done_uploading = False

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
        ui.buffer_layout.insert_line('Sending TC "(BL) Erase Golden in MRAM"')
        send_TC(
            "TC-" + conf["hex_upload"]["TC_erase_MRAM_GOLDEN_tag"],
            [],
            ui,
            resend_last_TC=False,
        )

    elif upload_type == "Application":
        # let's send the TC erase MRAM app
        ui.buffer_layout.insert_line('Sending TC "Erase Appli in MRAM"')
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
            "<error>Error: TM MRAM erased not received</error>"
        )
        error = True
    else:
        if upload_type == "Application":
            if TM_received["tag"] != conf["hex_upload"]["TM_MRAM_APP_erased_tag"]:
                ui.buffer_layout.insert_line(
                    "<error>Error: Was expecting TM MRAM erased</error>"
                )
                error = True

        else:
            if TM_received["tag"] != conf["hex_upload"]["TM_MRAM_GOLDEN_erased_tag"]:
                ui.buffer_layout.insert_line(
                    "<error>Error: Was expecting TM MRAM erased</error>"
                )
                error = True

    get_app().invalidate()
    info_message.remove_dialog_as_float(ui.root_container)

    if not error or ui.ser.test or args.loop:

        info_message = float_window.InfoDialog(
            f"{upload_type} Upload to SRU",
            "Upload in progress.. (2/3) \n(can take up to 30s)",
            ui.root_container,
        )
        get_app().invalidate()

        await asyncio.sleep(0.005)
        data = data.split("\n")

        ui.add_data_to_raw_window_enabled = False
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
                        pass
                        # sleep(conf["hex_upload"]["delay_inter_line"])
                        await asyncio.sleep(conf["hex_upload"]["delay_inter_line"])
                    else:
                        sleep(conf["hex_upload"]["delay_inter_line"])

        ui.add_data_to_raw_window_enabled = True

        # CRC calculation
        CRC_calculated = lib.compute_CRC_hex(data).zfill(2)
        ui.buffer_layout.insert_line(
            f"CRC calulated = 0x{CRC_calculated}. Sending CRC frame to SRU.."
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
                "<error>Error:</error> CRC frame from SRU not received."
            )
        else:
            await asyncio.sleep(0.005)  # async sleep to refresh UI
            try:
                if CRC_received["data"][1] != CRC_calculated:
                    error = True
                    ui.buffer_layout.insert_line(
                        f"<error>CRC ERROR: received 0x{CRC_received['data'][1]}, calculated 0x{CRC_calculated}</error>"
                    )
                else:
                    if upload_type == "Application":
                        if conf["hex_upload"]["send_TC_reboot_after_app_upload"]:

                            # Clearing the last_TM buffer
                            ui.clear_last_TM_buffer()

                            # Sending the TC Request Reload Appli
                            ui.buffer_layout.insert_line(
                                'Sending TC "Request Reload Appli from MRAM"'
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
                                    "<error>Error:</error> TM reloaded APP not received."
                                )
                            else:
                                if (
                                    TM_received["tag"]
                                    != conf["hex_upload"]["TM_reload_APP_tag"]
                                ):
                                    if not ui.ser.test:
                                        error = True
                                    ui.buffer_layout.insert_line(
                                        "<error>Error:</error> Was expecting TM reloaded APP."
                                    )
                                else:
                                    ui.buffer_layout.insert_line(
                                        'Sending TC "Reboot"'
                                    )
                                    send_TC(
                                        "TC-" + conf["hex_upload"]["TC_reboot_tag"],
                                        [],
                                        ui,
                                        resend_last_TC=False,
                                    )
                    else:
                        if conf["hex_upload"]["send_TC_reboot_after_golden_upload"]:
                            ui.buffer_layout.insert_line('Sending TC "Reboot"')
                            send_TC(
                                "TC-" + conf["hex_upload"]["TC_reboot_tag"] + "(BL)",
                                [],
                                ui,
                                resend_last_TC=False,
                            )
                    await asyncio.sleep(0.005)  # async sleep to refresh UI
            except IndexError:
                ui.buffer_layout.insert_line(
                    "<error>Error:</error> CRC frame from SRU is not correct."
                )

        info_message.remove_dialog_as_float(ui.root_container)
        get_app().invalidate()

        if not from_scenario and (not error or ui.ser.test or args.loop):
            float_window.show_message(
                f"{upload_type} Upload to SRU", "Upload done.", ui.root_container
            )

        ui.last_TC_sent["hex_upload"] = True
        ui.last_TC_sent["hex_file"] = data_backup
        ui.last_TC_sent["frame_bytes"] = False
        ui.last_TC_sent["bytes_only"] = False

        

        # Let's turn the watchdog back on
        if watchdog_value:
            ui.watchdog_radio.set_value(1)

        ui.done_uploading = True if (not error or ui.ser.test or args.loop) else "error"


def play_scenario(ui, scenario, on_startup):
    """Play a scenario
    
    Arguments:
        ui  -- UI instance
        scenario {list} -- Scenario to be played
        on_startup {bool} -- Whether it was called on startup or not 
    """


    # If scenario was called on startup,
    # let's wait for the UI to draw itself

    if on_startup:
        info_message = float_window.InfoDialog(
            "Scenario Mode",
            f"Scenario parsing is OK\nPlaying scenario in 1s..",
            ui.root_container,
        )
        get_app().invalidate()
        sleep(1)
        info_message.remove_dialog_as_float(ui.root_container)

    step_count = len([step for step in scenario if step["keyword"] != "//"])
    current_step = 1
    error = False

    for step in scenario:

        if step["keyword"] == "//":
            # If step is a comment, we print it to the TM/TC feed
            ui.buffer_layout.insert_line(f"Scenario mode: {step['comment']}")
        else:
            if step["keyword"] == "sleep":
                ui.buffer_layout.insert_line(
                    f"Scenario mode: sleeping <data>{step['argument']}s</data>"
                )

                info_message = float_window.InfoDialog(
                    "Scenario Mode",
                    f"Step {current_step}/{step_count}: \n    Type: sleep {step['argument']}s",
                    ui.root_container,
                )
                get_app().invalidate()

                sleep(step["argument"])
                info_message.remove_dialog_as_float(ui.root_container)

            elif step["keyword"] == "send":
                ui.buffer_layout.insert_line(
                    f"Scenario mode: sending <tc>{step['TC_tag']}</tc> with args <data>{step['TC_args']}</data>"
                )

                send_TC(step["TC_tag"], step["TC_args"], ui, resend_last_TC=False)

            elif step["keyword"] == "wait_tm":
                ui.clear_last_TM_buffer()
                ui.buffer_layout.insert_line(
                    f"Scenario mode: waiting for <tm>{step['TM_tag']}</tm> for <data>{step['timeout']}s</data> max"
                )
                info_message = float_window.InfoDialog(
                    "Scenario Mode",
                    f"Step {current_step}/{step_count}: \n    Type: wait for {step['TM_tag']} for {step['timeout']}s",
                    ui.root_container,
                )
                get_app().invalidate()

                TM_received = ui.wait_for_TM(timeout=step["timeout"])

                info_message.remove_dialog_as_float(ui.root_container)

                if not TM_received:
                    ui.buffer_layout.insert_line(
                        f"<error>Error:</error> {step['TM_tag']} was not received."
                    )
                    error = True
                    break

                elif TM_received["tag"] != step["TM_tag"].split("-")[1]:
                    ui.buffer_layout.insert_line(
                        f"<error>Error:</error> Received {TM_received}. Was expecting {step['TM_tag']}"
                    )
                    error = True
                    break

            elif step["keyword"] in ("app", "golden"):
                try:
                    with open(step["file"], "rb", buffering=0) as f:
                        data = f.readall()

                        upload_type = (
                            "Application" if step["keyword"] == "app" else "Golden"
                        )
                        call_from_executor(
                            lambda: asyncio.ensure_future(
                                upload_hex(ui, data, upload_type, from_scenario=True)
                            )
                        )
                        while not ui.done_uploading:
                            sleep(0.1)

                        # ui.buffer_layout.insert_line(str(ui.done_uploading))
                        if ui.done_uploading == "error":
                            error = True
                            break

                        ui.done_uploading = False

                except IOError as e:
                    float_window.show_message(
                        "Error", "{}".format(e), ui.root_container
                    )
                    get_app().invalidate()
                    error = True
                    break

            current_step += 1

    if args.quit_after_scenario:
        ui.application.exit()

    if not error:
        float_window.show_message("Scenario Mode", "Scenario done.", ui.root_container)
        
    else:
        float_window.show_message(
            "Scenario Mode", "Error in scenario !", ui.root_container
        )
    
    get_app().invalidate()


def send_bytes(ui, bytes_to_send):
    """Send custom bytes over serial link
    
    Arguments:
        ui  -- UI instance
        bytes_to_send {hex str} -- Bytes to send 
    """


    bytes_to_send = bytes_to_send.upper()
    bytes_to_send_bytearray = bytearray.fromhex(bytes_to_send)
    
    with ui.lock:
        if conf["COM"]["delay_inter_byte"] == 0 or args.socket:
            ui.ser.write(bytes_to_send_bytearray)
        else:
            for key, int_ in enumerate(bytes_to_send_bytearray):
                ui.ser.write([int_])
                if key != len(bytes_to_send_bytearray) - 1:
                    sleep(conf["COM"]["delay_inter_byte"])
        
        ui.buffer_layout.insert_line(f'Sent: 0x<tc>{bytes_to_send}</tc>')

    ui.last_TC_sent["bytes_only"] = True
    ui.last_TC_sent["frame_str"] = bytes_to_send
    ui.last_TC_sent['bytes'] = bytes_to_send