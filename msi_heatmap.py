#!/usr/bin/env python3
import argparse
import subprocess
import time
from collections import defaultdict

import Xlib.display
import Xlib.XK

from key_logger import KeyLogger

display = Xlib.display.Display()


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
    parser.add_argument('-g', '--end-color', action='store', default='ff0000', help='Base color for keys')

    parser.add_argument('-e', '--expire-time', action='store', default=60 * 60, help='Expire time of keystrokes')
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
