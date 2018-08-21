from time import sleep
import json
import sys
import lib
from prompt_toolkit.application.current import get_app
from lib import BD


def serial_com_TM(ser, lock, buffer_layout, TM_window):
    with lock:
        buffer_layout.text = "Waiting for sync word..."
        # while not ser.read(2).hex() in ("1234", "4321"):
        #     pass


        while True:
            first_byte = ser.read(1).hex()
            if first_byte in ("12", "43"):
                second_byte = ser.read(1).hex()
                if (first_byte == "12" and second_byte == "34") or (first_byte == "43" and second_byte == "21"):
                    break

        buffer_layout.text += "found ! \n"

        first_frame_data_lenght = int.from_bytes(ser.read(1), "big")

        ser.read(first_frame_data_lenght + 2)

    while True:
        # TM
        # FIXME read(1) call, and when it succeeds use read(inWaiting())
        *sync_word, data_lenght = ser.read(3)  # for no reason ser.read returns int here..
        sync_word = [format(_, "x") for _ in sync_word]

        tag, *data, CRC = [format(_, "x") for _ in ser.read(data_lenght + 2)]

        tag = str(tag) if len(str(tag)) > 1 else str(tag) + "0"
        try:
            frame_name = BD[tag]["name"]
            frame_data = BD[tag]["data"]
        except KeyError:
            frame_name = "Frame unrecognized"
            frame_data = False

        buffer_layout.text += lib.format_frame(
            "".join(sync_word), format(data_lenght, "x"), tag, "".join(data), CRC, frame_name
        )

        if frame_data:
            pointer = 0
            for value in frame_data:
                field_lenght = int(value[0])
                field_name = value[1]

                buffer_layout.text += (
                    " " + field_name + ": " + "".join(data[pointer : pointer + field_lenght])
                )
                pointer = pointer + field_lenght

        buffer_layout.text += "\n"

        if not get_app().layout.has_focus(TM_window):
            buffer_layout._set_cursor_position(len(buffer_layout.text) - 1)

        sleep(0.01)


def serial_com_TC(ser, lock, buffer_layout, watchdog_radio):
    while True:
        if watchdog_radio.current_value:
            frame_to_be_sent = (
                BD["01"]["header"]
                + BD["01"]["length"]
                + BD["01"]["tag"]
                + BD["01"]["data"]
                + BD["01"]["CRC"]
            )

            with lock:
                ser.write(frame_to_be_sent.encode())
                buffer_layout.text += lib.format_frame(
                    BD["01"]["header"],
                    BD["01"]["length"],
                    BD["01"]["tag"],
                    BD["01"]["data"],
                    BD["01"]["CRC"],
                    BD["01"]["name"],
                )
                buffer_layout.text += "\n"
            sleep(1)