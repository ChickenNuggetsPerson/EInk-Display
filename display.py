import sys
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont, ImageOps

import logging
import os
import platform

dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
Bfont = ImageFont.truetype('./Dangrek-Regular.ttf', 55, encoding="unic")
Mfont = ImageFont.truetype('./Dangrek-Regular.ttf', 45, encoding="unic")
Sfont = ImageFont.truetype('./Dangrek-Regular.ttf', 35, encoding="unic")
SSmono = ImageFont.truetype('./SourceCodePro-VariableFont_wght.ttf', 18, encoding="unic")
Smono = ImageFont.truetype('./SourceCodePro-VariableFont_wght.ttf', 20, encoding="unic")
Mmono = ImageFont.truetype('./SourceCodePro-VariableFont_wght.ttf', 30, encoding="unic")
Bmono = ImageFont.truetype('./SourceCodePro-VariableFont_wght.ttf', 40, encoding="unic")
subFont = ImageFont.truetype('./LexendGiga-VariableFont_wght.ttf', 30, encoding="unic")
subSubFont = ImageFont.truetype('./LexendGiga-VariableFont_wght.ttf', 20, encoding="unic")


import pandas as pd
from retry_requests import retry

from datetime import datetime, timedelta, timezone

import io
import math
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import PIL.ImageOps  
import calendar
import time

from mcstatus import JavaServer, BedrockServer

# logging.basicConfig(level=logging.DEBUG)

def main():

    image = genImage()

    if (platform.system() == "Darwin"):
        image = image.save("out.jpg")
    else:
        
        from waveshare_epd import epd7in5_V2 as disp
        epd = disp.EPD()
        epd.init()
        #epd.Clear()

        epd.display(epd.getbuffer(image))
        epd.sleep()







def genImage(width=800, height=480):
    Himage = Image.new('1', (width, height), 255)

    draw = ImageDraw.Draw(Himage)
    
    getCalendar(draw)
    getWeather(draw)
    getMCStatus(draw)

    now = datetime.now()
    day_name = now.strftime("%A")  # Full weekday name
    date_str = now.strftime("%B %d, %Y")
    time_str = now.strftime("%I:%M %p")

    SSmono.set_variation_by_name("ExtraLight")

    draw.text((15, 80), day_name, 'black', subFont)
    draw.text((10, 0), date_str, 'black', Bfont)
    draw.line((10, 120, 300, 120), fill='black', width=2)

    draw.text((5, 475), f"Refreshed at: {time_str}", 'black', SSmono, anchor="lb")

    return Himage




def getWeather(draw: ImageDraw.ImageDraw):
    

    if (len(sys.argv) == 1):
        print("Fetching Weather")

        currentCommand = """curl -s "https://wttr.in/Syracuse+Utah?0FQT" > data/current.txt """
        os.system(currentCommand)

        time.sleep(2)

        dayCommand = """curl -s "https://wttr.in/Syracuse+Utah?1FQTn" > data/day.txt """
        os.system(dayCommand)

    else:
        print("Skipping Weather Fetch")

    # Read files
    f = open("data/current.txt", "r")
    current = f.read()
    f.close()

    f = open("data/day.txt", "r")
    day = f.read()
    f.close()


    day = day.replace(current, "")
    SSmono.set_variation_by_name("Bold")
    draw.text((400, 360), day, "black", SSmono, anchor="mm")

def getCalendar(draw: ImageDraw.ImageDraw):

    x = 550
    y = 40

    width = 250
    height = 170

    i = 0

    now = datetime.now()
    month = calendar.monthcalendar(now.year, now.month)
    today = now.day

    days = [ "S", "M", "T", "W", "T", "F", "S" ]

    draw.line((x - 10, y + 12, x + width - 25, y + 12), "black", 1)

    subFont.set_variation_by_name("Bold")

    for day in days:
        draw.text((
            x + ( (i % 7) * ( 1 / 7 ) * width ), 
            y + ( (i // 7) * ( 1 / len(month) * height ) )
        ), day, "black", SSmono, anchor="mm")

        i += 1
    
    subFont.set_variation_by_name("Regular")

    for row in month:
        for day in row:

            i += 1

            if (day == 0): 
                continue

            if (day == today):

                SSmono.set_variation_by_name("Bold")

                # draw.circle((
                #     x + ( (i % 7) * ( 1 / 7 ) * width ), 
                #     y + ( (i // 7) * ( 1 / len(month) * height ) + 1)
                # ), 15, "white", "black", 1)

                draw.line(( 
                    x + ( (i % 7) * ( 1 / 7 ) * width ) - 10, 
                    y + ( (i // 7) * ( 1 / len(month) * height ) ) + 10,
                    x + ( (i % 7) * ( 1 / 7 ) * width ) + 10, 
                    y + ( (i // 7) * ( 1 / len(month) * height ) ) + 10
                ), "black", 2)

            else:   

                SSmono.set_variation_by_name("Regular")

            draw.text((
                x + ( (i % 7) * ( 1 / 7 ) * width ), 
                y + ( (i // 7) * ( 1 / len(month) * height ) )
            ), str(day), "black", SSmono, anchor="mm")

def getMCStatus(draw: ImageDraw.ImageDraw):


    x = 10
    y = 140


    jLatency = -1
    bLatency = -1

    try: 

        ip = "minecraft.steeleinnovations.com"
        jServer = JavaServer.lookup(ip)
        bServer = BedrockServer.lookup(ip)

        jLatency = round(jServer.status().latency, 1)
        bLatency = round(bServer.status().latency, 1)
    
    except: 
        pass

    draw.text((x + 5, y + 5), "Java:", "black", subSubFont)
    draw.text((x + 5, y + 40), "Bedrock:", "black", subSubFont)

    if (jLatency == -1):
        
        draw.rectangle((
            x + 130, 
            y, 
            x + 240, 
            y + 37
        ), "black")

        draw.text((x + 140, y + 7), "Offline", "white", subSubFont)

    else:
        draw.text((x + 140, y + 7), "Online", "black", subSubFont)


    if (bLatency == -1):
        
        draw.rectangle((
            x + 130, 
            y + 37, 
            x + 240, 
            y + 75
        ), "black")

        draw.text((x + 140, y + 44), "Offline", "white", subSubFont)

    else:
        draw.text((x + 140, y + 44), "Online", "black", subSubFont)


try:
    main()
except KeyboardInterrupt:
    print("Ctrl-C Entered")
    from waveshare_epd import epd7in5_V2 as disp
    disp.epdconfig.module_exit()
    sys.exit()