import threading
import time
from threading import Condition

import win32clipboard

class clipboard():
    def __init__(self, key_word_url):
        self.url = key_word_url
        self.thread = threading.Thread(target=self.monitor_clipboard, daemon=True)
        self.condition = Condition()
        self.copy_url = ""

    def start(self):
        self.thread.start()

    def get_clipboard_text(self):
        win32clipboard.OpenClipboard()
        try:
            data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
        except:
            return ""
        finally:
            win32clipboard.CloseClipboard()
        try:
            if isinstance(data, bytes):
                return data.decode("utf-8")
        except:
            return ""

    def get_url(self):
        with self.condition:
            self.condition.wait()
            return self.copy_url

    def monitor_clipboard(self):
        last_data = ""
        while True:
            current_data = self.get_clipboard_text()
            if current_data != last_data:

                last_data = current_data
                if current_data.startswith(self.url):
                    self.copy_url = current_data
                    with self.condition:
                        self.condition.notify()
                        print("clipboard notify")
            time.sleep(2)

if __name__ == "__main__":
    cb = clipboard("https://e-hentai.org/g/")
    cb.start()
    print(cb.get_url())