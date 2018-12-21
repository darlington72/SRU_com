import float_window

tools_list = [
    (0, "Reload App (MRAM & Flash)"),
    (1, "Reload GOLDEN in MRAM"),
    (2, "Load GOLDEN in boot mode"),
]


def tools_handler(UI):
    if UI.tools_selectable_list.current_value == 0:
        send_hex_to_MRAM(UI)
    elif UI.tools_selectable_list.current_value == 1:
        reload_GOLDEN_in_MRAM(UI)
    elif UI.tools_selectable_list.current_value == 2:
        load_GOLDEN_in_boot_mode(UI)


def send_hex_to_MRAM(UI):
    float_window.do_upload_hex(UI)

    # [x] Erase MRAM with parameter app
    # [ ] Upload app to MRAM with first parameter AA
    # [ ] Send wrong CRC TC with first parameter AA, wait for anwser, get CRC computed by SRU
    # [ ] Compute CRC of local hex and compare
    # [ ] if ok, send TC CRC with first parameter AA with CRC
    # [ ] send reload app MRAM

    # To deal with <ctrl> + R
    UI.last_TC_sent["hex_upload"] = True


def reload_GOLDEN_in_MRAM(UI):
    pass

    # [ ] Erase MRAM with parameter golden
    # [ ] Upload golden to MRAM with first parameter 55
    # [ ] Send wrong CRC TC with first parameter TT, wait for anwser, get CRC computed by SRU
    # [ ] Compute CRC of local hex and compare


def load_GOLDEN_in_boot_mode(UI):
    pass
    # [ ] same as reload_GOLDEN_in_MRAM but with different TC

