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
num_tendrils = num_strands - 1

fps = 30.0  # approximate measurement

# Pattern constants
# Time for the backdrop hue to ramp up and down
backdrop_ramp_time = 30.0 # seconds
hue_offset_per_strip = 0.15 / num_strands
backdrop_min = 0.2
backdrop_max = 0.8 - (hue_offset_per_strip * num_strands)

seconds_between_ripples = 3


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

# Ripple location on each tendril, measured in elements
# (no ripples on the head)
ripple_locs = [0] * num_tendrils
ripples_running = False
frames_since_ripples = 0

def draw_hue_backdrop(strips):
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


def draw_ripples(strips):
    global ripple_locs
    global ripples_running
    global frames_since_ripples

    num_segs = strand_length // 6

    if ripples_running:
        ripples_done = [False] * num_tendrils
        for (strip_idx, strip) in enumerate(strips[:num_tendrils]):
            ripple_loc = ripple_locs[strip_idx]

            # Only render the ripple of it's within the strand range
            if ripple_loc < 0:
                pass
            elif ripple_loc < num_segs:
                # Work out colour of less bright trailing seg
                trail_colour = strip[0]
                trail_colour = tuple(min(x + 64, 255) for x in trail_colour)

                for i in range(6):
                    # Brightest segment
                    strip[ripple_loc * 6 + i] = (255, 255, 255)

                if ripple_loc >= 1:
                    for i in range(6):
                        strip[(ripple_loc - 1) * 6 + i] = trail_colour
                if ripple_loc <= num_segs - 2:
                    for i in range(6):
                        strip[(ripple_loc + 1) * 6 + i] = trail_colour
            else:
                ripples_done[strip_idx] = True

            ripple_locs[strip_idx] += 1

        if ripples_done == [True] * num_tendrils:
            # Ripples done for this time
            ripples_running = False
            frames_since_ripples = 0

    else:
        if frames_since_ripples > fps * seconds_between_ripples:
            # Setup ripples to start again next frame
            ripples_running = True
            ripple_locs = [-5, -10, -15, -20, -25]
        frames_since_ripples += 1


while True:
    draw_hue_backdrop(strips)
    draw_ripples(strips)
    for strip in strips:
        strip.show()
