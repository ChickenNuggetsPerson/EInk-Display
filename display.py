import subprocess
import sys
import traceback
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont

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


import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import calendar

import requests
import json
from dotenv import load_dotenv

import requests

# logging.basicConfig(level=logging.DEBUG)

# Get GridPoint key https://api.weather.gov/points/{long},{lat}


def main():

    load_dotenv()  # Load environment variables from .env

    image = None

    if (len(sys.argv) > 1):
        if (validFilePath(sys.argv[1])):
            image = Image.open(sys.argv[1])
            image = image.convert("1")
        else:
            image = genImage()
    else:
        image = genImage()

    if (platform.system() == "Darwin"):
        image = image.save("out.jpg")
    else:

        from waveshare_epd import epd7in5_V2 as disp
        epd = disp.EPD()
        
        # if (fastMode):
        #     epd.init_fast()
        # else: 
        epd.init()

        epd.display(epd.getbuffer(image))
        epd.sleep()


def validFilePath(path_string: str):
    if (not path_string.endswith(".png")):
        return False
    
    if os.path.exists(path_string):
        if os.path.isfile(path_string):
            return True
        else:
            return False
    else:
        return False
    

def genImage(width=800, height=480):
    Himage = Image.new('1', (width, height), 255)
    draw = ImageDraw.Draw(Himage)
    
    now = datetime.now()
    day_name = now.strftime("%A")  # Full weekday name
    date_str = now.strftime("%B %d, %Y")
    time_str = now.strftime("%I:%M %p")

    if len(sys.argv) > 1:
        if (sys.argv[1] == "rebooted"):

            draw.rounded_rectangle((100, 100, 700, 380), radius=15, fill="white", outline="black")
            draw.text((400, 140), "System Rebooted", 'black', Bfont, anchor="mm")
            draw.line((150, 170, 650, 170), fill="black", width=2)

            draw.text((400, 200), date_str, 'black', subSubFont, anchor="mm")
            draw.text((400, 230), time_str, 'black', subSubFont, anchor="mm")

            ip = get_local_ip()
            ssid = get_ssid()

            draw.text((400, 300), f"SSID:   {ssid}", "black", subSubFont, anchor="mm")
            draw.text((400, 330), f"IP:     {ip}", "black", subSubFont, anchor="mm")

            return Himage

    getWeather(draw, Himage, True)
    getNetwork(draw)

    SSmono.set_variation_by_name("ExtraLight")
    subFont.set_variation_by_name("Bold")

    draw.text((15, 70), day_name, 'black', subFont)
    draw.text((10, 0), date_str, 'black', ImageFont.truetype('./Dangrek-Regular.ttf', 48, encoding="unic"))
    draw.line((10, 110, 300, 110), fill='black', width=2)

    draw.text((798, 2), time_str, 'black', SSmono, anchor="rt")

    return Himage


def getWeather(draw: ImageDraw.ImageDraw, image: Image.Image, includeNow: bool):
    
    yPos = 300

    if (len(sys.argv) == 1):
        try:
            print("Fetching Weather")

            office = os.getenv("WEATHER_FORECAST_OFFICE")
            gridX = os.getenv("WEATHER_GRID_X")
            gridY = os.getenv("WEATHER_GRID_Y")
            url = f"https://api.weather.gov/gridpoints/{office}/{gridX},{gridY}/forecast/hourly"

            apiData = requests.get(url).json()

            with open("data/data.json", "w") as f:
                json.dump(apiData, f, indent=4)
        except:
            print("Could not fetch weather")

    else:
        print("Skipping Weather Fetch")


    
    locationName = os.getenv("WEATHER_LOCATION_NAME")

    # Read file
    data = readJSON("data/data.json")
    periods = data["properties"]["periods"]
    
    draw.text((25, yPos - 35), locationName, "black", subSubFont, anchor="lb")
    draw.line((20, yPos - 30, 25 + len(locationName) * 15, yPos - 30), fill="black", width=1)

    # Screen width is 800
    dx = 800 / 6
    shift = dx / 2

    offset = 0
    if (includeNow):
        offset = 3
    

    index = -1
    for hour in periods[offset:6+offset]: # Only do the next 6 hours
        index += 1

        time = datetime.fromisoformat(hour["startTime"])
        timestr = time.strftime("%l %p").strip()
        draw.text((index * dx + shift, yPos), timestr, "black", subSubFont, anchor="mm")

        icon = getWeatherIcon(hour["icon"])
        size = 100 # - (index * 5)
        pasteIcon(image, icon, index * dx + 65, yPos + 70, size, size)

        temp = hour["temperature"]
        draw.text((index * dx + shift, yPos + 141 ), f"{temp}°", "black", SSmono, anchor="mm")

        if (index != 0):
            draw.line((index * dx, yPos + 5, index * dx, yPos + 145), fill="black", width=1)

        if (hour["probabilityOfPrecipitation"]["value"]):
            prob = hour["probabilityOfPrecipitation"]["value"]

            if (prob >= 10):
                draw.text((index * dx + shift, yPos + 160), f"{prob}%", "black", SSmono, anchor="mm")
            

    if (offset == 0):
        return

    current = periods[2]

    draw.rounded_rectangle((430, 20, 770, 270), radius=15, fill="white", outline="black")

    draw.text((600, 30), "Current Weather:", "black", Sfont, anchor="mt")
    draw.line((470, 60, 730, 60), fill="black", width=1)
    
    lines = wrapText(current["shortForecast"], 22, 2)

    for i, line in enumerate(lines):
        draw.text(
            (600, 195 + i * 30 - (len(lines) - 1) * 15 ), 
            line, 
            "black", 
            ImageFont.truetype('./LexendGiga-VariableFont_wght.ttf', 20, encoding="unic"), 
            anchor="mt"
        )


    temp = current["temperature"]
    temp = f"{temp}°"
    if (current["probabilityOfPrecipitation"]):
        prob = current["probabilityOfPrecipitation"]["value"]
        if (prob >= 10):
            temp = temp + f" - {prob}%"

    draw.text((600, 250), temp, "black", subSubFont, anchor="mt")

    icon = getWeatherIcon(current["icon"])
    size = 110
    pasteIcon(image, icon, 600, 120, size, size)


def get_local_ip():
    import socket

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "No IP"

def get_ssid():

    try:
        # Linux
        wifi_output = subprocess.check_output(["/usr/sbin/iwgetid", "-r"]).decode("utf-8")
        with open("data/ssid.txt", "w") as f:
                f.write(wifi_output.strip())
        return wifi_output.strip()

    except:
        return "Error Finding Wifi SSID" # Return an error message if none work
    

def getNetwork(draw: ImageDraw.ImageDraw):
    x = 20
    y = 145

    ip = get_local_ip()
    ssid = get_ssid()

    draw.text((x, y), f"SSID:   {ssid}", "black", SSmono, anchor="lt")
    y += 22
    draw.text((x, y), f"IP:     {ip}", "black", SSmono, anchor="lt")

def pasteIcon(image: Image.Image, icon: Image.Image, x, y, sx, sy):
    icon = icon.resize((int(sx), int(sy)))
    image.paste(icon, ( int(x - (sx/2)), int(y - (sy/2)) ), icon)

def getCalendar(draw: ImageDraw.ImageDraw):

    x = 520
    y = 40

    width = 270
    height = 190

    i = 0

    now = datetime.now()
    month = calendar.monthcalendar(now.year, now.month)
    today = now.day

    days = [ "S", "M", "T", "W", "T", "F", "S" ]

    draw.line((x - 10, y + 12, x + width - 25, y + 12), "black", 1)

    SSmono.set_variation_by_name("Bold")

    for day in days:
        draw.text((
            x + ( (i % 7) * ( 1 / 7 ) * width ), 
            y + ( (i // 7) * ( 1 / len(month) * height ) )
        ), day, "black", SSmono, anchor="mm")

        i += 1

    if (month[0].count(0) == 6):
        i -= 7

    for row in month:
        for day in row:

            i += 1

            if (day == 0): 
                continue

            if (day == today):

                SSmono.set_variation_by_name("Bold")

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



NOAA_ICON_MAP = {
    "skc": "sunny.png",
    "few": "cloudy_partial.png",
    "sct": "cloudy_partial.png",
    "bkn": "cloudy.png",
    "ovc": "cloudy.png",
    "wind_skc": "wind.png",
    "wind_few": "wind.png",
    "wind_sct": "wind.png",
    "wind_bkn": "wind.png",
    "wind_ovc": "wind.png",
    "snow": "snow.png",
    "rain_snow": "snow.png",
    "rain_sleet": "snow.png",
    "snow_sleet": "snow.png",
    "fzra": "rain.png",
    "rain_fzra": "rain.png",
    "snow_fzra": "snow.png",
    "sleet": "snow.png",
    "rain": "rain.png",
    "rain_showers": "rain_partial.png",
    "rain_showers_hi": "rain_partial.png",
    "tsra": "thunder.png",
    "tsra_sct": "thunder.png",
    "tsra_hi": "thunder.png",
    "tornado": "thunder.png",
    "hurricane": "wind.png",
    "tropical_storm": "wind.png",
    "dust": "fog.png",
    "smoke": "fog.png",
    "haze": "fog.png",
    "hot": "sunny.png",
    "cold": "snow.png",
    "blizzard": "snow.png",
    "fog": "fog.png",
}

def getWeatherIcon(icon_url):
    path = icon_url.split("icons/")[1].split("?")[0]   # e.g. "land/night/tsra_hi"
    parts = path.split("/")
    
    tod = parts[1]       # "day" or "night"
    condition = parts[2] # e.g. "tsra_hi"

    icon = NOAA_ICON_MAP.get(condition, "fog.png")

    # swap to night version if needed
    if tod == "night":
        if icon == "sunny.png":
            icon = "night.png"
        elif icon == "cloudy_partial.png":
            icon = "cloudy_partial_night.png"
        elif icon == "rain_partial.png":
            icon = "rain_partial_night.png"

    return Image.open(f"icons/pngs/{icon}")

def wrapText(text: str, maxChars: int, maxLines: int):
    currentStr = ""
    strs = [] 

    for word in text.split(" "):
        if (len(currentStr) + len(word) > maxChars):
            strs.append(currentStr.strip())
            currentStr = ""
        
        currentStr += " " + word
    
    if (currentStr.strip() != ""):
        strs.append(currentStr.strip())

    if len(strs) > maxLines:
        strs = strs[0:maxLines]
        line = strs[len(strs) - 1]
        strs[len(strs) - 1] = line + "..."

    return strs



try:
    main()
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
    from waveshare_epd import epd7in5_V2 as disp
    disp.epdconfig.module_exit()
    sys.exit()