#!/usr/bin/env python3
import argparse
import subprocess
import time
from collections import defaultdict
import pyxhook

import Xlib.display
import Xlib.XK

display = Xlib.display.Display()


class KeyLogger:
    """ This class capture the keystrokes. I hope you understand the implications of this :)
    """

    def __init__(self, expire_time_s=60 * 60):
        self.new_hook = pyxhook.HookManager()
        self.new_hook.KeyDown = self.on_key
        self.new_hook.HookKeyboard()
        self.new_hook.start()
        self.counter = KeyCounter(expire_time_s)

    def on_key(self, event):
        self.counter.press(event.Key)

    def stats(self):
        return self.counter.press_counts()


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


class Colors:
    @staticmethod
    def color_gradient(rgb1, rgb2, n):
        dRGB = [float(x2 - x1) / (n - 1) for x1, x2 in zip(rgb1, rgb2)]
        gradient = [tuple([int(x + k * dx) for x, dx in zip(rgb1, dRGB)]) for k in range(n)]
        return gradient

    @staticmethod
    def hex_to_rgb(value):
        value = value.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

    @staticmethod
    def rgb_to_hex(rgb):
        return '%02x%02x%02x' % rgb


class ConfigWriter:
    @staticmethod
    def reset_config(cfg_file, base_color_hex):
        with open(cfg_file, 'w') as cfg:
            cfg.write("%s steady %s\n" % ("all", base_color_hex))

    @staticmethod
    def write_config(cfg_file, base_color_hex, end_color_hex, config):
        rgb1 = Colors.hex_to_rgb(base_color_hex)
        rgb2 = Colors.hex_to_rgb(end_color_hex)
        gradient = Colors.color_gradient(rgb1, rgb2, 10)
        with open(cfg_file, 'w') as cfg:
            counter = 0
            for k, v in sorted(config.items()):
                # linear, TODO make exp
                color = gradient[int(10 / len(config) * counter)]

                rgb = Colors.rgb_to_hex(color)
                keys = ",".join(map(str, v))
                cfg.write("%s steady %s\n" % (keys, rgb))
                counter += 1


def change_color(cfg_file):
    subprocess.call(["msi-perkeyrgb", "-m", "GS65", "-c", cfg_file])


def to_linux_event_map(map):
    linux_keys = {display.keysym_to_keycode(Xlib.XK.string_to_keysym(key)): value for key, value in map.items()}
    new_dict = defaultdict(list)
    for k, v in linux_keys.items():
        # TODO ??
        if k == 0 or k == 187:
            continue
        new_dict[v].append(k)
    return dict(new_dict.items())


def main():
    parser = argparse.ArgumentParser(description='Heatmap for key presses')
    parser.add_argument('-c', '--color', action='store', default='ffe6e6', help='Base color for keys')
    parser.add_argument('-g', '--end-color', action='store', default='ff0000',
                        help='The color for the most intense key')

    parser.add_argument('-e', '--expire-time', action='store', default=60 * 60,
                        help='Expire time of keystrokes (seconds)')
    parser.add_argument('-u', '--update-interval', action='store', default=30, help='Update interval of keyboard')

    args = parser.parse_args()
    cfg_file = '/tmp/heatmap.cfg'

    ConfigWriter.reset_config(cfg_file, args.color)
    change_color(cfg_file)

    logger = KeyLogger(args.expire_time)
    while True:
        time.sleep(args.update_interval)
        stats = logger.stats()
        cfg = to_linux_event_map(stats)
        ConfigWriter.write_config(cfg_file, args.color, args.end_color, cfg)
        change_color(cfg_file)


if __name__ == '__main__':
    main()
