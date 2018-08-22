from prompt_toolkit import Application
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit import HTML
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.widgets import TextArea
import threading
import time

# Global key bindings.
bindings = KeyBindings()

@bindings.add("c-c", eager=True)
@bindings.add("c-q", eager=True)
def _(event):
    event.app.exit()



buffer = Buffer()

root_container =  Window(content=FormattedTextControl(text='<b>Hello</b> world'))
# root_container =  Window(content=BufferControl(buffer=buffer))
root_container = TextArea(text='oui', focusable=False)
layout = Layout(root_container)

app = Application(layout= layout, full_screen=True, key_bindings=bindings)






def update_text():
    while True:
        # root_container.content.text += 'test'
        # # app.renderer.render(app, layout=layout)
        # app.renderer.
        # buffer.insert_text(HTML('test'))
        root_container.content = HTML('<b>test</b>')
        time.sleep(1)


if __name__ == "__main__":

    lock = threading.Lock()

    thread1 = threading.Thread(target=update_text)
    
    thread1.daemon = True
    thread1.start()

    # thread1 = threading.Thread(target=lib.fill_buffer_debug, args=(buffer_layout,))
    # thread1.daemon = True
    # thread1.start()



    app.run()