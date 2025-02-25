import sys
from PIL import Image, ImageDraw, ImageFont

import logging
import os
import platform

dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
Bfont = ImageFont.truetype('./Dangrek-Regular.ttf', 55, encoding="unic")
Sfont = ImageFont.truetype('./Dangrek-Regular.ttf', 35, encoding="unic")
mono = ImageFont.truetype('./Mono.ttf', 20, encoding="unic")

logging.basicConfig(level=logging.DEBUG)


from datetime import datetime

def main():

    if (platform.system() == "Darwin"):
        pass
    else:
        
        from waveshare_epd import epd7in5_V2 as disp

        epd = disp.EPD()
        print(1)
        
        epd.init()
        print(2)

        epd.Clear()
        print(3)

        epd.sleep()
        print(4)



try:
    main()
except KeyboardInterrupt:
    print("Ctrl-C Entered")
    
    from waveshare_epd import epd7in5_V2 as disp
    disp.epdconfig.module_exit()
    
    sys.exit()