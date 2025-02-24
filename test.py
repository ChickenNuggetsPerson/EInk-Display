import sys
import time
from waveshare_epd import epd7in5_V2 as disp
from PIL import Image, ImageDraw, ImageFont

import logging
import os

dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
Bfont = ImageFont.truetype('./Dangrek-Regular.ttf', 55, encoding="unic")
Sfont = ImageFont.truetype('./Dangrek-Regular.ttf', 35, encoding="unic")

#logging.basicConfig(level=logging.DEBUG)

try:
    epd = disp.EPD()
    epd.init()
#    epd.Clear()

    Himage = Image.new('1', (epd.width, epd.height), 255)
    draw = ImageDraw.Draw(Himage)

    draw.text((10, 0), "Sunday", 'black', Bfont)
    draw.text((10, 80), "Febuary 23, 2025", 'black', Sfont)

    epd.display(epd.getbuffer(Himage))

    epd.sleep()
    print("Sleeping")


except KeyboardInterrupt:
    print("Ctrl-C Entered")
    disp.epdconfig.module_exit()
    sys.exit()
