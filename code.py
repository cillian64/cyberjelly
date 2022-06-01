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

fps = 30  # approximate measurement

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

# Ripple location on each tendril, measured in elements
# (no ripples on the head)
ripple_locs = [0] * num_tendrils
ripples_running = False
frames_to_ripple = 0

angry = False

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
        if angry:
            rgb[0] = max(rgb[0], 128)
            rgb[2] = 0
        strip.fill(rgb)


def draw_ripples(strips):
    global ripple_locs
    global ripples_running
    global frames_to_ripple

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
                if angry:
                    trail_colour = (255, 64, 0)
                else:
                    trail_colour = strip[0]
                    trail_colour = tuple(min(x + 64, 255) for x in trail_colour)

                for i in range(6):
                    # Brightest segment
                    if angry:
                        strip[ripple_loc * 6 + i] = (255, 0, 0)
                    else:
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

            # Randomise time to next ripple, unless angry
            if not angry:
                frames_to_ripple = random.randint(140, 400)
            else:
                frames_to_ripple = random.randint(10, 20)

    else:
        frames_to_ripple -= 1

        if frames_to_ripple <= 0:
            # Setup ripples to start again next frame
            ripples_running = True

            # If angry, all ripples are synced, otherwise random
            if angry:
                ripple_locs = [random.randint(-2, 0) for _ in range(num_tendrils)]
            else:
                ripple_locs = [random.randint(-20, 0) for _ in range(num_tendrils)]


def draw_angry(strips):
    """Make the jellyfish angry! """

    # First, make the head a red-ish colour
    colour = strips[num_tendrils][0]
    colour = (255, colour[1] // 4, 0)
    strips[num_tendrils].fill(colour)


while True:
    draw_hue_backdrop(strips)
    draw_ripples(strips)

    if angry:
        draw_angry(strips)

    for strip in strips:
        strip.show()
