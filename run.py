#!/usr/bin/env python
"""Launch GLIDE.

Usage:
    python run.py              # start at the menu
    python run.py --smoke      # headless self-test: solves level 1, exits 0
    python run.py --shot       # render a screenshot offscreen and exit
    python run.py --debug      # show the frame-rate meter
"""

import argparse

from panda3d.core import load_prc_file_data


def main():
    parser = argparse.ArgumentParser(description="GLIDE")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--shot", action="store_true")
    parser.add_argument("--shot-out", default=None)
    parser.add_argument("--gif", default=None, help="capture gameplay frames to this dir")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    load_prc_file_data("", "window-title GLIDE")
    load_prc_file_data("", "framebuffer-multisample 1")
    load_prc_file_data("", "multisamples 4")
    if args.smoke or args.shot or args.gif:
        load_prc_file_data("", "window-type offscreen")
        load_prc_file_data("", "audio-library-name null")
    if args.shot:
        load_prc_file_data("", "win-size 1280 720")
    if args.gif:
        load_prc_file_data("", "win-size 900 560")
    if args.debug:
        load_prc_file_data("", "show-frame-rate-meter true")

    from glide.app import GlideApp

    app = GlideApp(debug=args.debug, smoke=args.smoke,
                   shot=args.shot, shot_out=args.shot_out,
                   gif=bool(args.gif), gif_dir=args.gif)
    app.run()


if __name__ == "__main__":
    main()
