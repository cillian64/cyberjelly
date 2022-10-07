# Cyberjelly control code
# Copyright (c) 2022 David Turner
# This work is free. You can redistribute it and/or modify it under the
# terms of the Do What The Fuck You Want To Public License, Version 2,
# as published by Sam Hocevar. See the LICENSE file for more details.

import random
import board
import hsv

from adafruit_led_animation.helper import PixelMap
from neopio import NeoPIO


# Customize for your strands here.  The tentacles should be connected to the
# first `num_strands - 1` outputs, while the final output is connected to the
# LED strip inside the jellyfish's head.
num_strands = 6  # Number of LED strands, including tentacles and head
strand_length = 30  # Number of pixels per strand
brightness = 0.8  # Between 0.0 and 1.0

num_tentacles = num_strands - 1
fps = 60  # Approximate measurement, used for timing

# Pattern constants
# Time for the backdrop hue to ramp up and down
backdrop_ramp_time = 30.0  # seconds
hue_offset_per_strip = 0.15 / num_strands
backdrop_min = 0.2
backdrop_max = 0.8 - (hue_offset_per_strip * num_strands)

# Make the object to control the pixels
pixels = NeoPIO(board.GP0, board.GP1, board.GP2, num_strands*strand_length,
                num_strands=num_strands, auto_write=False, brightness=1)

# Make a virtual PixelMap so that each strip can be controlled independently
strips = [PixelMap(pixels, range(i*strand_length, (i+1)*strand_length),
                   individual_pixels=True) for i in range(num_strands)]

# State for the pattern
# Ranges between 0.2 and 0.6 going back and forth in a sawtooth
hue_backdrop = 0.2
hue_backdrop_increasing = True

# Ripple location on each tentacle, measured in elements
# (no ripples on the head)
ripple_locs = [0] * num_tentacles
ripples_running = False
frames_to_ripple = 0


def draw_hue_backdrop(strips):
    """ Fill each tentacle/strip with a solid colour.  The colours are
    determined by a hue which fades back and forth between purple and green.
    Each strip gets a slightly different hue. """
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


def draw_ripples(strips):  # noqa: disable C901
    """ Draw some white ripples which quickly run down all of the strips.  The
    ripple appears at a slightly different location on each strip. """
    global ripple_locs
    global ripples_running
    global frames_to_ripple

    # On the original cyberjellies, each tentacle was made up of segments
    # where each segment contained 6 LEDs.  On the mini-jellies each segment
    # is only a single LED pixel.
    num_segs = strand_length

    if ripples_running:
        ripples_done = [False] * num_tentacles
        # We have more strips than tentacles (the LED strip in the jellyfish
        # head shouldn't have ripples), so only draw ripples on the tentacles
        # and not on the head.
        for (strip_idx, strip) in enumerate(strips[:num_tentacles]):
            ripple_loc = ripple_locs[strip_idx]

            # Only render the ripple of it's within the strand range
            if ripple_loc < 0:
                pass
            elif ripple_loc < num_segs:
                # Work out colour of less bright trailing seg
                trail_colour = strip[0]
                trail_colour = tuple(min(x + 64, 255) for x in trail_colour)

                # Brightest segment
                strip[ripple_loc] = (255, 255, 255)

                if ripple_loc >= 1:
                    strip[ripple_loc - 1] = trail_colour
                if ripple_loc <= num_segs - 2:
                    strip[ripple_loc + 1] = trail_colour
            else:
                ripples_done[strip_idx] = True

            ripple_locs[strip_idx] += 1

        if ripples_done == [True] * num_tentacles:
            # Ripples done for this time
            ripples_running = False

            # Randomise time to next ripple
            frames_to_ripple = random.randint(140, 400)

    else:
        frames_to_ripple -= 1

        # Check if it is time for a new ripple
        if frames_to_ripple <= 0:
            # Setup ripples to start again next frame
            ripples_running = True
            ripple_locs = [random.randint(-20, 0)
                           for _ in range(num_tentacles)]


while True:
    # First, draw the solid hue on each strip then overlay the ripples on top
    draw_hue_backdrop(strips)
    draw_ripples(strips)

    # Render to the LED driver
    for strip in strips:
        strip.show()
