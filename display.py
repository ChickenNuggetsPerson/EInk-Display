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

import requests
import json
from dotenv import load_dotenv

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
    getWeather(draw, Himage)
    getMCStatus(draw)

    now = datetime.now()
    day_name = now.strftime("%A")  # Full weekday name
    date_str = now.strftime("%B %d, %Y")
    time_str = now.strftime("%I:%M %p")

    SSmono.set_variation_by_name("ExtraLight")

    draw.text((15, 80), day_name, 'black', subFont)
    draw.text((10, 0), date_str, 'black', Bfont)
    draw.line((10, 120, 300, 120), fill='black', width=2)

    draw.text((1, 479), f"Refreshed at: {time_str}", 'black', SSmono, anchor="lb")

    return Himage




def getWeather(draw: ImageDraw.ImageDraw, image: Image.Image):
    

    if (len(sys.argv) == 1):
        print("Fetching Weather")

        load_dotenv()  # Load environment variables from .env

        apiKey = os.getenv("ACCUWEATHER_API_KEY")
        locationKey = os.getenv("ACCUWEATHER_LOCATION_KEY")
        url = f"http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/{locationKey}?apikey={apiKey}"

        apiData = requests.get(url).json()

        with open("data/data.json", "w") as f:
            json.dump(apiData, f, indent=4)

    else:
        print("Skipping Weather Fetch")

    # Read file
    data = readJSON("data/data.json")

    # Screen width is 800
    dx = 800 / 6
    shift = dx / 2

    index = -1
    for hour in data[:6]: # Only do the next 6 hours
        index += 1

        time = datetime.fromisoformat(hour["DateTime"])
        timestr = time.strftime("%l %p").strip()
        draw.text((index * dx + shift, 285), timestr, "black", subSubFont, anchor="mm")

        icon = getWeatherIcon(hour["WeatherIcon"], hour["IsDaylight"])
        image.paste(icon, (int(index * dx + 15), 310), icon)

        temp = hour["Temperature"]["Value"]
        draw.text((index * dx + shift, 426), f"{temp}°", "black", SSmono, anchor="mm")

        if (hour["PrecipitationProbability"]):
            prob = hour["PrecipitationProbability"]

            if (prob >= 10):
                draw.text((index * dx + shift, 445), f"{prob}%", "black", SSmono, anchor="mm")





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

    # subFont.set_variation_by_name("Bold")
    SSmono.set_variation_by_name("Bold")

    for day in days:
        draw.text((
            x + ( (i % 7) * ( 1 / 7 ) * width ), 
            y + ( (i // 7) * ( 1 / len(month) * height ) )
        ), day, "black", SSmono, anchor="mm")

        i += 1

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





def readJSON(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in: {file_path}")
        return None
def getWeatherIcon(icon_code, isDaylight):
    name = ""
    
    if icon_code in [1, 2, 3, 30]: 
        name = "sunny.png"

    elif icon_code in [33, 34, 35]:
        name = "night.png"

    elif icon_code in [4, 5, 6, 36, 37, 38]:  # Partly Cloudy
        
        if isDaylight:
            name = "cloudy_partial.png"
        else:
            name = "cloudy_partial_night.png"

    elif icon_code in [39, 40]:  # Partial Rain

        if isDaylight:
            name = "rain_partial.png"
        else:
            name = "rain_partial_night.png"

    elif icon_code in [7, 8]:  # Cloudy
        name = "cloudy.png"

    elif icon_code in [11]: # Fog
        name = "fog.png"

    elif icon_code in [12, 13, 14, 18]:  # Rain
        name = "rain.png"

    elif icon_code in [15, 16, 17, 41, 42]:  # Thunderstorms
        name = "thunder.png"

    elif icon_code in [19, 20, 21, 22, 23, 24, 25, 26, 29, 31, 43, 44]:  # Snow
        name = "snow.png"

    elif icon_code in [32]:  # Snow
        name = "wind.png"

    else:
        print("Code:", icon_code)
        name = "fog.png"

    im = Image.open(f"icons/pngs/{name}")
    return im.resize((100, 100), Image.Resampling.NEAREST)

try:
    main()
except KeyboardInterrupt:
    print("Ctrl-C Entered")
    from waveshare_epd import epd7in5_V2 as disp
    disp.epdconfig.module_exit()
    sys.exit()