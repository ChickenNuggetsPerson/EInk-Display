import sys
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont

import logging
import os
import platform

dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
Bfont = ImageFont.truetype('./Dangrek-Regular.ttf', 55, encoding="unic")
Mfont = ImageFont.truetype('./Dangrek-Regular.ttf', 45, encoding="unic")
Sfont = ImageFont.truetype('./Dangrek-Regular.ttf', 35, encoding="unic")
SSmono = ImageFont.truetype('./SourceCodePro-VariableFont_wght.ttf', 15, encoding="unic")
Smono = ImageFont.truetype('./SourceCodePro-VariableFont_wght.ttf', 20, encoding="unic")
Mmono = ImageFont.truetype('./SourceCodePro-VariableFont_wght.ttf', 30, encoding="unic")
Bmono = ImageFont.truetype('./SourceCodePro-VariableFont_wght.ttf', 40, encoding="unic")
subFont = ImageFont.truetype('./LexendGiga-VariableFont_wght.ttf', 30, encoding="unic")


import pandas as pd
from retry_requests import retry

from datetime import datetime, timedelta, timezone

import io
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import asyncio
import PIL.ImageOps  

from mcstatus import JavaServer, BedrockServer

# logging.basicConfig(level=logging.DEBUG)

async def main():

    image = await genImage()

    if (platform.system() == "Darwin"):
        image = image.save("out.jpg")
    else:
        
        from waveshare_epd import epd7in5_V2 as disp
        epd = disp.EPD()
        epd.init()
        #epd.Clear()

        epd.display(epd.getbuffer(image))
        epd.sleep()







async def genImage(width=800, height=480):
    Himage = Image.new('1', (width, height), 255)

    data = await getWeather()
    Himage.paste(data)

    draw = ImageDraw.Draw(Himage)

    now = datetime.now()
    day_name = now.strftime("%A")  # Full weekday name
    date_str = now.strftime("%B %d, %Y")
    time_str = now.strftime("%R %p")

    draw.text((10, 80), day_name, 'black', subFont)
    draw.text((10, 0), date_str, 'black', Bfont)
    draw.text((800, 5), "Refreshed at:", 'black', SSmono, anchor="rt")
    draw.text((790, 25), time_str, 'black', SSmono, anchor="rt")

    draw.line((10, 130, 300, 130), fill='black', width=3)

    return Himage





async def getWeather():
    
    

    # Make images
    Himage = Image.new('1', (800, 480), 255)
    draw = ImageDraw.Draw(Himage)


    # Recomment back in
    # currentCommand = """curl -s "https://wttr.in/Syracuse+Utah?0FQT" > data/current.txt """
    # os.system(currentCommand)

    # dayCommand = """curl -s "https://wttr.in/Syracuse+Utah?1FQTn" > data/day.txt """
    # os.system(dayCommand)

    # Read files
    f = open("data/current.txt", "r")
    current = f.read()
    f.close()

    f = open("data/day.txt", "r")
    day = f.read()
    f.close()


    day = day.replace(current, "")
    draw.text((400, 395), day, "black", SSmono, anchor="mm")

    
    # server = "minecraft.steeleinnovations.com"
    # javaStatus = JavaServer.lookup(server)
    # bedrockStatus = BedrockServer.lookup(server)

    # javaStatus.status().


    return Himage


try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Ctrl-C Entered")
    from waveshare_epd import epd7in5_V2 as disp
    disp.epdconfig.module_exit()
    sys.exit()