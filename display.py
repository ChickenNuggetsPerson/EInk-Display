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

def main():

    load_dotenv()  # Load environment variables from .env

    image = None
    fastMode = False

    if (len(sys.argv) > 1):
        if (validFilePath(sys.argv[1])):
            image = Image.open(sys.argv[1])
            image = image.convert("1")
            fastMode = True
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

    drawRandImage = False

    if drawRandImage:
        Himage = fetchRandomImage()

    draw = ImageDraw.Draw(Himage)
    
    now = datetime.now()

    if (not drawRandImage):
        getCalendar(draw)
        getWeather(draw, Himage)
        getNetwork(draw)
    
        day_name = now.strftime("%A")  # Full weekday name
        date_str = now.strftime("%B %d, %Y")

        SSmono.set_variation_by_name("ExtraLight")

        draw.rounded_rectangle((5, 20, 10 + len(day_name) * 55, 120), radius=10, fill="white")
        draw.text((15, 80), day_name, 'black', subFont)
        draw.text((10, 0), date_str, 'black', Bfont)
        draw.line((10, 120, 300, 120), fill='black', width=2)

    time_str = now.strftime("%I:%M %p")
    draw.text((798, 2), time_str, 'black', SSmono, anchor="rt")

    return Himage


def fetchLocationData():

    print("Location Key Changed, Fetching New Location Data")
    apiKey = os.getenv("ACCUWEATHER_API_KEY")
    locationKey = os.getenv("ACCUWEATHER_LOCATION_KEY")
    url = f"http://dataservice.accuweather.com/locations/v1/{locationKey}?apikey={apiKey}"

    apiData = requests.get(url).json()
    with open("data/location.json", "w") as f:
        json.dump({
            "for": locationKey,
            "data": apiData
        }, f, indent=4)

def getWeather(draw: ImageDraw.ImageDraw, image: Image.Image):
    
    yPos = 300

    if (len(sys.argv) == 1):
        try:
            print("Fetching Weather")

            apiKey = os.getenv("ACCUWEATHER_API_KEY")
            locationKey = os.getenv("ACCUWEATHER_LOCATION_KEY")
            url = f"http://dataservice.accuweather.com/forecasts/v1/hourly/12hour/{locationKey}?apikey={apiKey}"

            apiData = requests.get(url).json()

            with open("data/data.json", "w") as f:
                json.dump(apiData, f, indent=4)
        except:
            print("Could not fetch weather")

    else:
        print("Skipping Weather Fetch")


    # Read location file
    location = readJSON("data/location.json")
    if (location is None):
        fetchLocationData()
        location = readJSON("data/location.json")
    else:
        if (location["for"] != os.getenv("ACCUWEATHER_LOCATION_KEY")):
            fetchLocationData()
            location = readJSON("data/location.json")

    # Read file
    data = readJSON("data/data.json")
    

    locationName = location["data"]["LocalizedName"] + ", " + location["data"]["AdministrativeArea"]["LocalizedName"]
    draw.text((25, yPos - 35), locationName, "black", subSubFont, anchor="lb")
    draw.line((20, yPos - 30, 25 + len(locationName) * 15, yPos - 30), fill="black", width=1)

    # Screen width is 800
    dx = 800 / 6
    shift = dx / 2

    offset = 0

    now = datetime.now()
    if (now.hour >= 21 or now.hour <= 5):
        offset = 1
    

    index = -1
    for hour in data[offset:6+offset]: # Only do the next 6 hours
        index += 1

        time = datetime.fromisoformat(hour["DateTime"])
        timestr = time.strftime("%l %p").strip()
        draw.text((index * dx + shift, yPos), timestr, "black", subSubFont, anchor="mm")

        icon = getWeatherIcon(hour["WeatherIcon"], hour["IsDaylight"])
        size = 100 # - (index * 5)
        pasteIcon(image, icon, index * dx + 65, yPos + 70, size, size)

        temp = hour["Temperature"]["Value"]
        draw.text((index * dx + shift, yPos + 141 ), f"{temp}°", "black", SSmono, anchor="mm")

        if (index != 0):
            draw.line((index * dx, yPos + 5, index * dx, yPos + 145), fill="black", width=1)

        if (hour["PrecipitationProbability"]):
            prob = hour["PrecipitationProbability"]

            if (prob >= 10):
                draw.text((index * dx + shift, yPos + 160), f"{prob}%", "black", SSmono, anchor="mm")
            

    if (offset == 0):
        return

    current = data[0]

    draw.rounded_rectangle((430, 20, 770, 270), radius=15, fill="white", outline="black")

    draw.text((600, 30), "Current Weather:", "black", Sfont, anchor="mt")
    draw.line((470, 60, 730, 60), fill="black", width=1)
    
    draw.text((600, 200), current["IconPhrase"], "black", subFont, anchor="mt")
    temp = current["Temperature"]["Value"]
    temp = f"{temp}°"
    if (current["PrecipitationProbability"]):
        prob = current["PrecipitationProbability"]
        if (prob >= 10):
            temp = temp + f" - {prob}%"

    draw.text((600, 240), temp, "black", subSubFont, anchor="mt")

    icon = getWeatherIcon(current["WeatherIcon"], current["IsDaylight"])
    size = 110
    pasteIcon(image, icon, 600, 125, size, size)


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

    return Image.open(f"icons/pngs/{name}")

def fetchRandomImage(): 
    response = requests.get("https://picsum.photos/800/480")
    with open("data/image.png", "wb") as f:
        f.write(response.content)

    image = Image.open("data/image.png").convert("L", dither=Image.Dither.FLOYDSTEINBERG)  # Convert to grayscale
    image = image.convert("1")
    return image



try:
    main()
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
    from waveshare_epd import epd7in5_V2 as disp
    disp.epdconfig.module_exit()
    sys.exit()