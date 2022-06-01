# SPDX-FileCopyrightText: 2021 Jeff Epler for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import random
import board
import hsv

from adafruit_led_animation.helper import PixelMap
from neopio import NeoPIO


# Customize for your strands here
num_strands = 6
strand_length = 114

fps = 60.0  # approximate measurement

# Pattern constants
# Time for the backdrop hue to ramp up and down
backdrop_ramp_time = 30.0 # seconds
hue_offset_per_strip = 0.15 / num_strands
backdrop_min = 0.2
backdrop_max = 0.8 - (hue_offset_per_strip * num_strands)


# Make the object to control the pixels
pixels = NeoPIO(board.GP0, board.GP1, board.GP2, num_strands*strand_length,
    num_strands=num_strands, auto_write=False, brightness=1)

# Make a virtual PixelMap so that each strip can be controlled independently
strips = [PixelMap(pixels, range(i*strand_length, (i+1)*strand_length), individual_pixels=True)
    for i in range(num_strands)]

# State for the pattern
# Ranges between 0.2 and 0.6 going back and forth in a sawtooth
hue_backdrop = 0.2
hue_backdrop_increasing = True

def render(strips):
    global hue_backdrop_increasing
    global hue_backdrop

    if hue_backdrop_increasing:
        hue_backdrop += 1.0 / (fps * backdrop_ramp_time)
        if hue_backdrop >= backdrop_max:
            hue_backdrop_increasing = False
    else:
        hue_backdrop -= 1.0 / (fps * backdrop_ramp_time)
        if hue_backdrop <= backdrop_min:
            hue_backdrop_increasing = True

    for (strip_idx, strip) in enumerate(strips):
        h = hue_backdrop + strip_idx * hue_offset_per_strip
        rgb = hsv.hsv_to_rgb(h, 1.0, 1.0)
        rgb = [int(255 * x) for x in rgb]
        strip.fill(rgb)

while True:
    render(strips)
    for strip in strips:
        strip.show()
