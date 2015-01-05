#!/usr/bin/env python
"""Extract text from ocropus outputs.

This concatenates the individual text fragments, from left to right and then
top to bottom.

It orders the fragments by y-midpoint, then uses x coordinates to order
overlapping fragments.

Input is a lines.json file (from ocropus-gpageseg --output_json).
Output is text, printed to stdout.
"""

import json
import os
import sys


def overlapping(a, b):
    """Two lines are overlapping if >50% of either is in the other."""
    overlap = min(a['y2'], b['y2']) - max(a['y1'], b['y1'])
    height = min(a['y2'] - a['y1'], b['y2'] - b['y1'])
    return 1.0 * overlap / height > 0.5


def sort_lines(lines):
    lines = lines[:]

    # First, sort by y-midpoint
    lines.sort(key=lambda line: (line['y1'] + line['y2']) * 0.5)

    # If a line is entirely to the left of the one preceding it, and they
    # overlap vertically, then they're out of order.
    i = 0
    while i < len(lines) - 1:
        a = lines[i]
        b = lines[i + 1]
        if b['x2'] < a['x1'] and overlapping(a, b):
            lines[i], lines[i + 1] = b, a
            i = 0
        else:
            i += 1

    for a, b in zip(lines[:-1], lines[1:]):
        if overlapping(a, b):
            b['continuation'] = True

    return lines


def attach_text(lines):
    lines = lines[:]
    for line in lines:
        path = line['file'].replace('.bin.png', '.txt')
        txt = ''
        try:
            txt = open(path).read()
        except IOError:
            sys.stderr.write('%s is missing\n' % path)
        if txt:
            line['text'] = txt.strip()
    return lines


if __name__ == '__main__':
    _, json_path = sys.argv
    lines = json.load(open(json_path))['lines']
    lines = sort_lines(lines)
    lines = attach_text(lines)

    output = ''
    for idx, line in enumerate(lines):
        if idx > 0:
            if line.get('continuation'):
                output += '  '
            else:
                output += '\n'
        if 'text' in line:
            output += line['text']

    print output
