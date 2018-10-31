import time
import readchar


class KeyCounter:
    def __init__(self, expire_time=30):
        self.expire_time = expire_time
        self.counter = {}

    def press(self, ch):
        if ch not in self.counter:
            self.counter[ch] = []
        self.counter[ch].append(time.time())

    def evict(self):
        for key, value in self.counter.items():
            self.counter[key] = list(filter(lambda x: x > time.time() - self.expire_time, value))

    def press_counts(self):
        self.evict()
        return {key: len(value) for key, value in self.counter.items()}


if __name__ == '__main__':
    k = KeyCounter(2000)
    c = 0
    while c < 10:
        a = repr(readchar.readchar())
        k.press(a)
        c += 1
    print(k.press_counts())
