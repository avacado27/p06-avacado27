# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

import math

from tornado.testing import gen_test

from tests.base import FilterTestCase

RADIUS = 50
MAX_RGB_DIFFERENCE = 8
# Boundary band: pixels whose centre lies between RADIUS - 2 and RADIUS
# from the corner's arc centre. Chosen from geometry, not from alpha.
BAND_INNER = RADIUS - 2
BAND_OUTER = RADIUS


def boundary_pixels(radius):
    """Pixels in the top-left corner box that lie on the arc band.

    Selected by geometry only, so the result does not depend on the
    alpha values the filter wrote.
    """
    pixels = []
    for y in range(radius):
        for x in range(radius):
            d = math.hypot(x + 0.5 - radius, y + 0.5 - radius)
            if BAND_INNER <= d <= BAND_OUTER:
                pixels.append((x, y))
    return pixels


class RoundCornerAntialiasTestCase(FilterTestCase):
    @gen_test
    async def test_antialiased_edge_keeps_rgb_and_partial_alpha(self):
        image = await self.get_filtered(
            "source.jpg",
            "thumbor.filters.round_corner",
            f"round_corner({RADIUS},255,0,0,1)",
            mode="RGBA",
        )
        source = self.get_fixture("source.jpg", mode="RGB")

        boundary = boundary_pixels(RADIUS)
        assert boundary, "no boundary pixels found from corner geometry"

        # Check RGB on every boundary pixel, whatever its alpha.
        darkened = []
        for x, y in boundary:
            r, g, b, a = image.getpixel((x, y))
            sr, sg, sb = source.getpixel((x, y))
            diff = max(abs(r - sr), abs(g - sg), abs(b - sb))
            if diff > MAX_RGB_DIFFERENCE:
                darkened.append((x, y, a, (r, g, b), (sr, sg, sb), diff))

        # Diagnostic values for the report.
        src_45_0 = source.getpixel((45, 0))
        out_45_0 = image.getpixel((45, 0))
        alphas = [image.getpixel(p)[3] for p in boundary]
        partial_count = sum(1 for a in alphas if 0 < a < 255)

        assert not darkened, (
            f"{len(darkened)} of {len(boundary)} boundary pixels have RGB "
            f"off by more than {MAX_RGB_DIFFERENCE}; first: {darkened[:3]}; "
            f"pixel (45,0) output={out_45_0} source={src_45_0}"
        )
        assert partial_count > 0, (
            "no boundary pixel has partial alpha (0 < alpha < 255); "
            f"boundary alphas seen: {sorted(set(alphas))}"
        )
