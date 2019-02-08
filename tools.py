import float_window
import serial_com

tools_list = [(0, "Reload App (MRAM)"), (1, "Load GOLDEN in boot mode")]


def tools_handler(UI):
    if UI.tools_selectable_list.current_value == 0:
        send_hex_to_MRAM(UI)
    elif UI.tools_selectable_list.current_value == 1:
        load_GOLDEN_in_boot_mode(UI)


def send_hex_to_MRAM(UI):
    float_window.do_upload_hex(UI, "Application")

    # [x] Erase MRAM with parameter app
    # [x] Upload app to MRAM
    # [ ] Send wrong CRC TC with first parameter AA, wait for anwser, get CRC computed by SRU. Actually not, need to calculate on SRU side
    # to prevent
    # [ ] Compute CRC of local hex and compare
    # [ ] if ok, send TC CRC with first parameter AA with CRC
    # [ ] send reload app MRAM

    # To deal with <ctrl> + R

    # add pourcentage avec tqdm
    UI.last_TC_sent["hex_upload"] = True


def load_GOLDEN_in_boot_mode(UI):

    float_window.do_upload_hex(UI, "Golden")
    # [x] send TC Erase MRAM Golden
    # [x] tempo 10s
    # [x] send golden

