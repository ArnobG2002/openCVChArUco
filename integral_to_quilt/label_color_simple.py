"""
Pick a label color that contrasts with an image.

    python label_color.py photo.jpg

Assumes the image is reasonably uniform in brightness and hue.
Requires: pillow
"""

import colorsys
import sys

from PIL import Image, ImageDraw, ImageFont, ImageStat


def contrasting_color(img):
    """Return an (r, g, b) label color that stands out against the image."""
    r, g, b = ImageStat.Stat(img.convert("RGB")).median
    print("image median color:", (r, g, b), "#%02x%02x%02x" % (r, g, b))
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)

    l = 1-l   # flip to the opposite end of lightness

    return tuple(int(c * 255) for c in colorsys.hls_to_rgb(h, l, s))


def main(path):
    img = Image.open(path).convert("RGB")
    color = contrasting_color(img)
    print("label color:", color, "#%02x%02x%02x" % color)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
    except OSError:
        font = ImageFont.load_default()

    draw = ImageDraw.Draw(img)
    draw.text((40, 40), "HELLO WORLD", fill=color, font=font)
    img.save("labeled.png")
    print("saved labeled.png")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "input.jpg")
