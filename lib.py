from time import sleep
import json
import sys

try:
    conf_file = open("conf.json", "r")
    conf = json.load(conf_file)
except FileNotFoundError:
    print("Configuration file 'conf.json' not found.")
    sys.exit()

try:
    BD_file = open("BD.json", "r")
    BD = json.load(BD_file)
except FileNotFoundError:
    print("BD file 'conf.json' not found.")
    sys.exit()


def format_frame(*frame):
    formatted_frame = " ".join(frame[:-1])
    formatted_frame = f"{formatted_frame:30} {frame[-1]}"
    return formatted_frame


def fill_buffer_debug(buffer):
    while True:
        buffer.text += "TM \n"
        sleep(1)
