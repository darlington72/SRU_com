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
import asyncio


use_asyncio_event_loop()

def do_exit():
    get_app().exit(result=False)


test_buffer = Buffer()




TM_window = Window(BufferControl(buffer=test_buffer, focusable=False))


verticalline1 = VerticalLine()

radios = RadioList(values=[
    (1, '1Hz'),
    (10, '10Hz'),
    (20, '20Hz')
])


async def update_TM():
    i = 1
    while True:
        test_buffer.text += '2017-07-19   15:30:25,2555   :::  TM' + str(i) + '\n'
        test_buffer._set_cursor_position(len(test_buffer.text)-1)
        i += 1
        await asyncio.sleep(1/radios.current_value)




root_container = VSplit([
    HSplit([
        Frame(body=Label(text=HTML('                  <b>TC Management</b>\n\n Content')), width=50),
        Frame(title='Data update freq', body=radios),
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
    """
    Pressing Ctrl-Q or Ctrl-C will exit the user interface.

    Setting a return value means: quit the event loop that drives the user
    interface and return this value from the `CommandLineInterface.run()` call.

    Note that Ctrl-Q does not work on all terminals. Sometimes it requires
    executing `stty -ixon`.
    """
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


def run():
    result = application.run()
    print('Bye bye.')


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(asyncio.gather(application.run_async().to_asyncio_future(), update_TM()))




