import json
import os

themes = {}
with open('./themes.json') as f:
	themes = json.load(f)

BLACK  = (12, 12, 12)
RED    = (197, 15, 31)
GREEN  = (19, 161, 14)
YELLOW = (193, 156, 0)
BLUE   = (0, 55, 218)
PURPLE = (136, 23, 152)
CYAN   = (58, 150, 221)
WHITE  = (204, 204, 204)
BIT8_COLORS = {0:BLACK, 1:RED, 2:GREEN, 3:YELLOW, 4:BLUE, 5:PURPLE, 6:CYAN, 7:WHITE}

LIGHT_BLACK  = (118, 118, 118)
LIGHT_RED    = (231, 72, 86)
LIGHT_GREEN  = (22, 198, 12)
LIGHT_YELLOW = (249, 241, 165)
LIGHT_BLUE   = (59, 120, 255)
LIGHT_PURPLE = (180, 0, 158)
LIGHT_CYAN   = (97, 214, 214)
LIGHT_WHITE  = (242, 242, 242)
BIT16_COLORS = {8:LIGHT_BLACK, 9:LIGHT_RED, 10:LIGHT_GREEN, 11:LIGHT_YELLOW, 12:LIGHT_BLUE, 13:LIGHT_PURPLE, 14:LIGHT_CYAN, 15:LIGHT_WHITE}
BIT16_COLORS.update(BIT8_COLORS)

BIT256_COLORS = {}


def add_rgb():
	r, g, b, i = 0, 0, 0, 16
	for _ in range(95, 335, 40):
		for _ in range(95, 335, 40):
			for _ in range(95, 335, 40):
				BIT256_COLORS[i] = (r, g, b)
				b = max(95, b+40)
				i += 1
			g = max(95, g+40)
			b = 0
		r = max(95, r+40)
		g = 0

def add_geyscale():
	i = 232
	r, g, b = 8, 8, 8
	for _ in range(24):
		BIT256_COLORS[i] = (r, g, b)
		r += 10
		g += 10
		b += 10
		i += 1

add_rgb()
add_geyscale()
BIT256_COLORS.update(BIT16_COLORS)

def bit256_color_converter(num):
	if num not in range(256):
		raise ValueError(str(num) + " is not in range 256")

	return BIT256_COLORS[num]
