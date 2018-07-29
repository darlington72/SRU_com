from time import sleep


def format_frame(*frame):
    formatted_frame = " ".join(frame[:-1])
    formatted_frame = f"{formatted_frame:30} {frame[-1]}"
    return formatted_frame


def fill_buffer_debug(buffer):
    while True:
        buffer.text += "TM \n"
        sleep(1)
