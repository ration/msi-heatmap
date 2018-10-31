import pyxhook

from key_counter import KeyCounter


class KeyLogger:
    """ This class capture the keystrokes. I hope you understand the implications of this :)
    """

    def __init__(self, expire_time_s=60*60):
        self.new_hook = pyxhook.HookManager()
        self.new_hook.KeyDown = self.on_key
        self.new_hook.HookKeyboard()
        # start the session
        self.new_hook.start()
        self.counter = KeyCounter(expire_time_s)

    def on_key(self, event):
        self.counter.press(event.Key)

    def stats(self):
        return self.counter.press_counts()
