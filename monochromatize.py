#!/bin/python

import os
import re
import subprocess

monochromatization_variant = 2 # variants: 1, 2, 3
dry_run = False

# color format conversions

# '#fff' -> ('ff', 'ff', 'ff')
def str2hex(col: str) -> tuple[str]:
    col = col.replace("#", "")
    col = "".join([2 * c for c in col]) if len(col) == 3 else col
    return tuple([col[i:i+2] for i in (0, 2, 4)])

# '255,255,255' -> (225,255,255)
def str2rgb(col: str) -> tuple[int]:
    return tuple([int(c) for c in col.split(",")])

# ('ff', 'ff', 'ff') -> '#ffffff'
def hex2str(col: tuple[str]) -> str:
    return "#" + "".join(col)

# (255,255,255) -> '255,255,255'
def rgb2str(col: tuple[int]) -> str:
    return ",".join([str(c) for c in col])

# ('ff', 'ff', 'ff') -> (255,255,255)
def hex2rgb(col: tuple[str]) -> tuple[int]:
    return tuple([int(c, 16) for c in col])

# (255,255,255) -> ('ff', 'ff', 'ff)
def rgb2hex(col: tuple[int]) -> tuple[str]:
    col = '%02x%02x%02x' % col
    return tuple([col[i:i+2] for i in (0, 2, 4)])

# brightness value
def val(col: str) -> int:
    return sum(hex2rgb(str2hex(col)))

# get colors from plasma color scheme: '#ffffff', ...
scheme = {
    "dark": subprocess.getoutput("kreadconfig5 --file kdeglobals --group Colors:View --key ForegroundNormal"),
    "light": subprocess.getoutput("kreadconfig5 --file kdeglobals --group Colors:View --key BackgroundNormal"),
    "accent": subprocess.getoutput("kreadconfig5 --file kdeglobals --group General --key AccentColor")
           or subprocess.getoutput("kreadconfig5 --file kdeglobals --group Colors:View --key DecorationFocus")
}
for color in scheme:
    if not scheme[color].startswith("#"):
        scheme[color] = hex2str(rgb2hex(str2rgb(scheme[color])))

# set light and dark colors
light = scheme["light"]
dark = scheme["accent"]
# dark = scheme["dark"]

# run through icon files
for root, dirs, files in os.walk(os.path.dirname(os.path.abspath(__file__))):
    for filename in files:
        filepath = os.path.join(root, filename)
        if any([blockword in filepath for blockword in 
            ["links", "colors", "symbolic", "mimetypes", "colorscheme"]]):
            continue
        if any([blockword in filename for blockword in
            ["black-", "blue-", "brown-", "green-", "grey-" "orange-", "pink-", "purple-", "red-", "yellow-"]]):
            continue
        if not filepath.endswith(".svg") or filepath.endswith("_.svg"):
            continue
        with open(filepath) as f:
            content = f.read()

        # find colors in svg: ['ffffff', ...]
        colors = re.findall(r"\"#([A-Fa-f0-9]{3}|[A-Fa-f0-9]{6})\"", content)
        if not colors:
            continue
        white = 'ffffff'
        middle = val(white) * 0.6
        values = sorted(list(set([val(color) for color in colors])))
        median = values[int(len(values)/2)]
        for color in colors:
            match monochromatization_variant:
                case 1:
                    # version 1: make the light/dark cut at 60% brightness
                    if val(color) < middle:
                        monochrome = dark
                    else:
                        monochrome = light
                    break
                case 2:
                    # version 2: make the light/dark cut at the median brightness of the occurring colors
                    if val(color) < median:
                        monochrome = dark
                    else:
                        monochrome = light
                    break
                case 3:
                    # version 3: continuous shades of brightness mapped from original colors
                    monochrome = hex2str(rgb2hex(tuple([min(255, max(0, int(c + (val(color) / val(white) * (255 - c))))) for c in  hex2rgb(str2hex(dark))])))
                    break
            # replace the color with the monochrome version
            content = content.replace("#" + color, monochrome)

        # write icon file with new content
        if dry_run:
            filepath = filepath.replace(".svg","_.svg")
        with open(filepath, "w") as f:
            f.write(content)
