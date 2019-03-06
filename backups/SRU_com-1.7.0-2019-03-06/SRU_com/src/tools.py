"""tools.py

Tools definition
"""

from prompt_toolkit import print_formatted_text

import src.float_window as float_window
import src.serial_com as serial_com

tools_list = [
    (0, "Reload App (MRAM)"),
    (1, "Load GOLDEN in boot mode"),
    (2, "Load a scenario"),
    (3, "Send bytes")
]


def tools_handler(ui):
    if ui.tools_selectable_list.current_value == 0:
        send_hex_to_MRAM(ui)
    elif ui.tools_selectable_list.current_value == 1:
        load_GOLDEN_in_boot_mode(ui)
    elif ui.tools_selectable_list.current_value == 2:
        load_scenario(ui)
    elif ui.tools_selectable_list.current_value == 3:
        send_bytes(ui)


def send_hex_to_MRAM(ui):
    float_window.do_upload_hex(ui, "Application")

    # [x] Erase MRAM with parameter app
    # [x] Upload app to MRAM
    # [ ] Send wrong CRC TC with first parameter AA, wait for anwser, get CRC computed by SRU. Actually not, need to calculate on SRU side
    # to prevent
    # [ ] Compute CRC of local hex and compare
    # [ ] if ok, send TC CRC with first parameter AA with CRC
    # [ ] send reload app MRAM

    # To deal with <ctrl> + R

    # add pourcentage avec tqdm
    ui.last_TC_sent["hex_upload"] = True


def load_GOLDEN_in_boot_mode(ui):
    float_window.do_upload_hex(ui, "Golden")
    ui.last_TC_sent["hex_upload"] = True


def load_scenario(ui):
    float_window.do_load_scenario(ui)

def send_bytes(ui):
    float_window.do_send_bytes(ui)