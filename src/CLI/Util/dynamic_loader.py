import time

from ...Util.common import count_cn_char


class DynamicLoader:
    def __init__(self, text: str, dots: int = 3) -> None:
        self.text = text
        self.dots = dots
        self.last_dot_count = 0

    def _print_once(self) -> None:
        print(self.text, end="", flush=True)
        print("." * (self.last_dot_count + 1), end="\r", flush=True)

    def _pp_once(self) -> None:
        self.last_dot_count = (self.last_dot_count + 1) % (self.dots + 1)

    def clear(self) -> None:
        print(
            " " * (count_cn_char(self.text) + len(self.text) + self.dots + 1),
            end="\r",
            flush=True,
        )

    def next(self) -> None:
        self._print_once()
        self._pp_once()
        if self.last_dot_count == 0:
            self.clear()
            self._print_once()
            self._pp_once()

    def next_for_times(self, times: int, interval: float) -> None:
        for _ in range(times):
            self.next()
            time.sleep(interval)
        self.clear()
