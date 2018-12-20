import float_window

tools_list = [(0, "Send HEX to MRAM"), (1, "Dump and Compare MRAM")]

def tools_handler(UI):
    if UI.tools_selectable_list.current_value == 0:
        send_hex_to_MRAM(UI)
    elif UI.tools_selectable_list.current_value == 1:
        dump_and_compare_MRAM(UI)


def send_hex_to_MRAM(UI):
    float_window.do_upload_hex(UI)

    # To deal with <ctrl> + R
    UI.last_TC_sent[3] = True

def dump_and_compare_MRAM(UI):
    pass
    