#!/usr/bin/env python
# -*- coding: ascii -*-

from __future__ import print_function

import argparse
import bisect
import os
import sys

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("matplotlib is required; install it with: sudo apt-get install python-matplotlib")
    sys.exit(1)


def read_log(filename):
    with open(filename, "r") as source:
        header = source.readline().strip()
        rows = []

        for line_number, line in enumerate(source, 2):
            fields = line.strip().split("\t")
            if len(fields) != 2:
                continue

            try:
                elapsed = float(fields[0].replace(",", "."))
                value = int(fields[1])
            except ValueError:
                raise ValueError("Invalid data at line %d" % line_number)

            rows.append((elapsed, value))

    if not rows:
        raise ValueError("No data rows found in %s" % filename)

    if "Stato GPIO" in header:
        kind = "gpio"
        description = "GPIO state"
    elif "Conteggio interrupt cumulativo" in header:
        kind = "counter"
        description = "Cumulative interrupt count"
    elif "Tempo callback" in header:
        kind = "events"
        description = "Interrupt callback events (callback-time pin state)"
    else:
        raise ValueError("Unsupported log format: %s" % header)

    return kind, description, rows


def draw_data(axis, kind, description, rows, start, end, title):
    times = [row[0] for row in rows]
    left = bisect.bisect_left(times, start)
    right = bisect.bisect_right(times, end)
    visible = rows[left:right]

    if kind == "gpio":
        if visible:
            axis.step(
                [row[0] for row in visible],
                [row[1] for row in visible],
                where="post"
            )
        axis.set_ylim(-0.2, 1.2)
        axis.set_yticks([0, 1])
    elif kind == "counter":
        before = bisect.bisect_left(times, start)
        initial_count = rows[before - 1][1] if before else 0
        plot_times = [start]
        plot_counts = [initial_count]
        for elapsed, count in visible:
            plot_times.append(elapsed)
            plot_counts.append(count)
        plot_times.append(end)
        plot_counts.append(plot_counts[-1])
        axis.step(plot_times, plot_counts, where="post")
        axis.set_ylabel("Interrupt count")
    else:
        if visible:
            event_times = [row[0] for row in visible]
            axis.vlines(event_times, 0, 1)
        axis.set_ylim(-0.1, 1.1)
        axis.set_yticks([])
        axis.set_ylabel("Events")

    axis.set_xlim(start, end)
    axis.set_title(title)
    axis.set_xlabel("Elapsed time (s)")
    axis.grid(True)


def main():
    parser = argparse.ArgumentParser(
        description="Plot a GPIO test log and a selected time interval."
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="./pin23_polling.txt",
        help="GPIO, cumulative interrupt, or interrupt-edge log"
    )
    parser.add_argument(
        "--start",
        type=float,
        default=0.0,
        help="start of zoom interval in seconds (default: 0)"
    )
    parser.add_argument(
        "--end",
        type=float,
        help="end of zoom interval in seconds (default: first second)"
    )
    parser.add_argument(
        "--save",
        help="save the figure to an image file instead of opening a window"
    )
    args = parser.parse_args()

    try:
        kind, description, rows = read_log(args.file)
    except (IOError, ValueError) as error:
        print("Error: %s" % error)
        return 1

    file_end = rows[-1][0]
    zoom_start = args.start
    zoom_end = args.end if args.end is not None else min(file_end, zoom_start + 1.0)

    if zoom_start < 0 or zoom_end <= zoom_start or zoom_start >= file_end:
        print("Error: zoom interval must be within the log duration.")
        return 1

    zoom_end = min(zoom_end, file_end)
    figure, (overview, detail) = plt.subplots(2, 1, sharex=False)
    figure.suptitle("%s - %s" % (os.path.basename(args.file), description))

    draw_data(
        overview, kind, description, rows, 0.0, file_end,
        "Full acquisition"
    )
    overview.axvspan(zoom_start, zoom_end, color="orange", alpha=0.25)
    draw_data(
        detail, kind, description, rows, zoom_start, zoom_end,
        "Detail: %.3f to %.3f seconds" % (zoom_start, zoom_end)
    )
    figure.tight_layout()

    if args.save:
        figure.savefig(args.save)
        print("Saved plot to %s" % args.save)
    else:
        plt.show()

    return 0


if __name__ == "__main__":
    sys.exit(main())
