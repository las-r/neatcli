import sys
import time
import itertools
import threading
from typing import List

# neatcli user interface engine
# by las-r

# ansi color escape sequences
CLR_RESET = "\033[0m"
CLR_BOLD = "\033[1m"
CLR_RED = "\033[31m"
CLR_GREEN = "\033[32m"
CLR_YELLOW = "\033[33m"
CLR_BLUE = "\033[34m"
CLR_CYAN = "\033[36m"
CLR_GRAY = "\033[90m"

class Spinner:
    def __init__(self, message: str = "Loading..."):
        self.message = message
        self.frames = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
        self.running = False
        self._thread = None

    def _spin(self):
        while self.running:
            sys.stdout.write(f"\r{CLR_CYAN}{next(self.frames)}{CLR_RESET} {self.message}")
            sys.stdout.flush()
            time.sleep(0.08)

    def __enter__(self):
        self.running = True
        
        # hide cursor
        sys.stdout.write("\033[?25l")
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.running = False
        if self._thread:
            self._thread.join()
            
        # clear line and show cursor
        sys.stdout.write("\r\033[K\033[?25h")
        sys.stdout.flush()

class ProgressBar:
    def __init__(self, message: str, total: int, width: int = 30):
        self.message = message
        self.total = total
        self.width = width
        self.current = 0

    def __enter__(self):
        sys.stdout.write("\033[?25l")
        self.update(0)
        return self

    def update(self, amount: int = 1):
        self.current = min(self.current + amount, self.total)
        percent = (self.current / self.total) if self.total > 0 else 0
        filled = int(self.width * percent)
        bar = "█" * filled + "░" * (self.width - filled)
        
        sys.stdout.write(f"\r{self.message}: [{CLR_GREEN}{bar}{CLR_RESET}] {int(percent * 100)}%")
        sys.stdout.flush()

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.write("\n\033[?25h")
        sys.stdout.flush()

class View:
    # color layout accessors
    RESET = CLR_RESET
    BOLD = CLR_BOLD
    RED = CLR_RED
    GREEN = CLR_GREEN
    YELLOW = CLR_YELLOW
    BLUE = CLR_BLUE
    CYAN = CLR_CYAN
    GRAY = CLR_GRAY

    @staticmethod
    def spinner(message: str = "Loading...") -> Spinner:
        return Spinner(message)

    @staticmethod
    def progress_bar(message: str, total: int, width: int = 30) -> ProgressBar:
        return ProgressBar(message, total, width)

    @staticmethod
    def table(headers: List[str], rows: List[List[str]]):
        # convert all fields to string format
        str_rows = [[str(cell) for cell in row] for row in rows]
        
        # calculate maximum col widths dynamically
        col_widths = [len(h) for h in headers]
        for row in str_rows:
            for idx, cell in enumerate(row):
                if idx < len(col_widths):
                    col_widths[idx] = max(col_widths[idx], len(cell))
                else:
                    col_widths.append(len(cell))

        # formatter logic helper
        def print_row(cells, color=""):
            line = ""
            for idx, cell in enumerate(cells):
                width = col_widths[idx]
                padded = f"{cell:<{width}}"
                line += f" {color}{padded}{CLR_RESET} |"
            print(f"|{line}")

        # construct separation barriers
        sep = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"

        # render output
        print(sep)
        print_row(headers, CLR_BOLD + CLR_CYAN)
        print(sep)
        for row in str_rows:
            print_row(row)
        print(sep)