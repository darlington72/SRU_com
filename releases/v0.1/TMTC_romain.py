from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.layout.containers import VSplit, HSplit
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.layout.layout import Layout, Window
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea, Label, Frame, Box, Checkbox, Dialog, Button, RadioList, MenuContainer, MenuItem, ProgressBar, VerticalLine
from pygments.lexers.html import HtmlLexer
from prompt_toolkit import HTML
from prompt_toolkit.layout import FormattedTextControl
from prompt_toolkit.eventloop import use_asyncio_event_loop
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.formatted_text import to_formatted_text
import threading
import serial
from huepy import *
import json
import sys
from time import sleep 


use_asyncio_event_loop()

def do_exit():
    get_app().exit(result=False)


test_buffer = Buffer()





TM_window = Window(BufferControl(buffer=test_buffer, focusable=True))


verticalline1 = VerticalLine()

watchdog_radio = RadioList(values=[
    (True, 'True'),
    (False, 'False')
])

def format_frame(*frame):
    formatted_frame = ' '.join(frame[:-1])
    formatted_frame = f"{formatted_frame:30} {frame[-1]}"
    return formatted_frame


def serial_com_TM(ser, lock):
    with open("BD.json", "r") as read_file:
        BD = json.load(read_file)   
    
        with lock:
            test_buffer.text = 'Waiting for sync word...'
            while not ser.read(2).hex() in ('1234', '4321'):
                pass

            test_buffer.text += 'found ! \n'
            

            first_frame_data_lenght = int.from_bytes(ser.read(1), 'big')

            ser.read(first_frame_data_lenght + 2)

        while True:
            # TM

            *sync_word, data_lenght = ser.read(3) # for no reason ser.read returns int here..
            sync_word = [format(_ , 'x') for _ in sync_word]

            tag, *data, CRC = [format(_, 'x') for _ in ser.read(data_lenght + 2)]

            try:
                frame_name = BD[tag]['name']
                frame_data = BD[tag]['data']
            except KeyError:
                frame_name = 'Frame unrecognized'
                frame_data = ''

            test_buffer.text += format_frame(''.join(sync_word), format(data_lenght, 'x'), tag, ''.join(data), CRC, frame_name)

            # test_buffer.text += ' '.join(frame_data)
            test_buffer.text += '\n'

            if not get_app().layout.has_focus(TM_window):
                test_buffer._set_cursor_position(len(test_buffer.text)-1)




def serial_com_TC(ser, lock):
    with open("BD.json", "r") as read_file:
        BD = json.load(read_file)
        while True:       
            if watchdog_radio.current_value:
                frame_to_be_sent = BD['01']['header'] + BD['01']['length'] + BD['01']['tag'] + BD['01']['data'] +  BD['01']['CRC'] 
                
                with lock:
                    ser.write(frame_to_be_sent.encode())
                    test_buffer.text += format_frame(BD['01']['header'], BD['01']['length'], BD['01']['tag'], BD['01']['data'], BD['01']['CRC'], BD['01']['name'])
                    test_buffer.text += '\n'
                sleep(1)


root_container = VSplit([
    HSplit([
        Frame(body=Label(text=HTML('                  <b>TC Management</b>\n\n Content')), width=50),
        Frame(title='Clear Watchdog', body=watchdog_radio),
    ], height=D()),
    verticalline1,
    TM_window,
])


# Global key bindings.
bindings = KeyBindings()
bindings.add('tab')(focus_next)
bindings.add('s-tab')(focus_previous)

@bindings.add('c-c', eager=True)
@bindings.add('c-q', eager=True)
def _(event):
    event.app.exit()



style = Style.from_dict({
    'window.border': '#888888',
    'shadow': 'bg:#222222',
    'window.border shadow': '#444444',

    'focused  button': 'bg:#880000 #ffffff noinherit',

    # Styling for Dialog widgets.

    'radiolist focused': 'noreverse',
    'radiolist focused radio.selected': 'reverse',
})


application = Application(
    layout=Layout(
        root_container,
    ),
    key_bindings=bindings,
    style=style,
    full_screen=True, 
    mouse_support=False)


def run_app():
    result = application.run()
    print('Bye bye.')


if __name__ == '__main__':

    lock = threading.Lock()

    ser = serial.Serial('/dev/ttyUSB0', 115200)
    thread1 = threading.Thread(target=serial_com_TM, args=(ser, lock))
    thread1.daemon = True
    thread1.start()

    thread1 = threading.Thread(target=serial_com_TC, args=(ser, lock))
    thread1.daemon = True
    thread1.start()


    run_app()


