from command_prompt import Window
from command_prompt import CursorShape
import time

window = Window()

class ProgressBar:
    def __init__(self, iterable, *, window, width=100):
        self.iterable = iterable
        self.width = width
        self.start_row = window.cursor_pos[0]
        self.start_time = 0

    def __iter__(self):
        window.change_cursor(CursorShape.INVISIBLE)
        self.current_num = 0
        self.start_time = time.time()
        time.sleep(0.005)
        return self

    def __next__(self):
        if not window.running or self.current_num >= len(self.iterable):
            window.change_cursor(CursorShape.BAR)
            raise StopIteration
        else:
            x = self.current_num
            self.current_num += 1
            window.delete_row()
            percentage = self.current_num / len(self.iterable)
            progress = int(self.width * percentage)
            progress_string = "[" + "=" * (progress-1) + ">" + " " * (self.width - progress) + "]"

            remaining = len(self.iterable) - self.current_num
            rate = self.current_num / (time.time() - self.start_time)

            remaining_seconds = 0
            if rate != 0:
                remaining_seconds = remaining / rate

            mins, secs = divmod(remaining_seconds, 60)
            window.print(f'{" "*(3-len(str(int(percentage*100))))}{int(percentage*100)}% {progress_string} {self.current_num}/{len(self.iterable)} eta [{str(int(mins)).rjust(2, "0")}:{str(int(secs)).rjust(2, "0")}]', add=True)
            return self.iterable[x]

def main():
    window.print(" Loading, please wait!\n", add=True)
    for _ in ProgressBar(range(100), window=window, width=88):
        time.sleep(.1)

window.run(main)
