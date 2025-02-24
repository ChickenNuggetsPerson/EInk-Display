import sys
from PIL import Image, ImageDraw, ImageFont

import logging
import os
import platform

dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
Bfont = ImageFont.truetype('./Dangrek-Regular.ttf', 55, encoding="unic")
Sfont = ImageFont.truetype('./Dangrek-Regular.ttf', 35, encoding="unic")
mono = ImageFont.truetype('./Mono.ttf', 20, encoding="unic")

#logging.basicConfig(level=logging.DEBUG)

import openmeteo_requests

import requests_cache
import pandas as pd
from retry_requests import retry

from datetime import datetime

import io
import math
import matplotlib.pyplot as plt

def main():

    image = genImage()

    if (platform.system() == "Darwin"):
        image = image.save("out.jpg")
    else:
        
        from waveshare_epd import epd7in5 as disp
        epd = disp.EPD()
        epd.init()
        #epd.Clear()

        epd.display(epd.getbuffer(image))
        epd.sleep()







def genImage(width=800, height=480):
    Himage = Image.new('1', (width, height), 255)

    data = getWeather()
    Himage.paste(data)

    draw = ImageDraw.Draw(Himage)

    now = datetime.now()
    day_name = now.strftime("%A")  # Full weekday name
    date_str = now.strftime("%B %d, %Y")

    draw.text((10, 0), day_name, 'black', Bfont)
    draw.text((10, 70), date_str, 'black', Sfont)

    # draw.line((10, 130, 300, 130), fill='black', width=3)

    return Himage





def getWeather():
    
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 41.0894,
        "longitude": 112.0647,
        "hourly": ["temperature_2m", "rain", "weather_code"],
        "daily": ["weather_code", "precipitation_probability_max", "temperature_2m_max", "temperature_2m_min"],
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "America/Denver"
    }
    responses = openmeteo.weather_api(url, params=params)


    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_rain = hourly.Variables(1).ValuesAsNumpy()
    hourly_weather_code = hourly.Variables(2).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}

    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["rain"] = hourly_rain
    hourly_data["weather_code"] = hourly_weather_code

    hourly_dataframe = pd.DataFrame(data = hourly_data)

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_weather_code = daily.Variables(0).ValuesAsNumpy()
    daily_precipitation_probability_max = daily.Variables(1).ValuesAsNumpy()
    daily_temperature_2m_max = daily.Variables(2).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(3).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
        end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = daily.Interval()),
        inclusive = "left"
    )}

    daily_data["weather_code"] = daily_weather_code
    daily_data["precipitation_probability_max"] = daily_precipitation_probability_max
    daily_data["temperature_2m_max"] = daily_temperature_2m_max
    daily_data["temperature_2m_min"] = daily_temperature_2m_min

    daily_dataframe = pd.DataFrame(data = daily_data)
    



    # Make images
    Himage = Image.new('1', (800, 480), 255)
    draw = ImageDraw.Draw(Himage)


    graph = makeDailyGraph(hourly_dataframe)
    w = 400
    graph = graph.resize((w, int((w / 5) * 3)))
    Himage.paste(graph, (400, 10), graph)


    for index, row in daily_dataframe.iterrows():

        day = weekDayFromNum(row.iloc[0].weekday())
        precipProb = round(row.iloc[2], 2)
        temp_max = int(row.iloc[3])
        temp_min = int(row.iloc[4])

        draw.text((
            (1.0 / 7.0) * index * 800 + 55, 
            280
        ), day, "black", Sfont, anchor="mm")

        draw.text((
            (1.0 / 7.0) * index * 800 + 55, 
            320
        ), f"{temp_max}°", "black", mono, anchor="mm")

        draw.text((
            (1.0 / 7.0) * index * 800 + 55, 
            320 + 25
        ), f"{temp_min}°", "black", mono, anchor="mm")

        draw.text((
            (1.0 / 7.0) * index * 800 + 50, 
            460
        ), f"{precipProb}%", "black", mono, anchor="mm")


        icon = Image.open(f"icons/pngs/{weatherImage(row.iloc[1])}")
        icon = icon.resize((75, 75))

        Himage.paste(icon, (
            int((1.0 / 7.0) * index * 800 + 17), 
            365
            ), icon
        )

    draw.line((10, 250, 790, 250), fill='black', width=1)


    # return {
    #     "hourly": hourly_dataframe,
    #     "daily": daily_dataframe
    # }

    return Himage



def weekDayFromNum(x):
    if (x == 0):
        return "Mon"
    if (x == 1):
        return "Tue"
    if (x == 2):
        return "Wed"
    if (x == 3):
        return "Thu"
    if (x == 4):
        return "Fri"
    if (x == 5):
        return "Sat"
    if (x == 6):
        return "Sun"
    return ""

def weatherImage(x):
    weather_codes = {
        0: "sunny",
        1: "sunny",
        2: "cloudy_partial",
        3: "cloudy",
        45: "fog",
        48: "fog",
        51: "rain_partial",
        53: "rain",
        55: "rain",
        56: "rain_partial",
        57: "rain",
        61: "rain_partial",
        63: "rain",
        65: "rain",
        66: "rain_partial",
        67: "rain",
        71: "snow", # light
        73: "snow", # moderate
        75: "snow", # heavy
        77: "snow", # grains
        80: "rain_partial",
        81: "rain",
        82: "rain",
        85: "snow", # Partial,
        86: "snow", # Heavy
        95: "thunder",
        96: "thunder",
        99: "thunder",
    }

    if x in weather_codes:
        return weather_codes[x] + ".png"
    else:
        return "Error"



def makeDailyGraph(data):
    
    # Himage = Image.new('1', (800, 480), 255)
    # draw = ImageDraw.Draw(Himage)

    # for index, row in data.iterrows():
        
    #     print(row)
    #     print()
        
    #     pass

    print(data)

    today = datetime.today().date()
    df_today = data[data['date'].dt.date == today]

    plt.figure(figsize=(5, 3))
    plt.plot(df_today['date'], df_today['temperature_2m'], linestyle='-', color='b')
    
    plt.xlabel('')
    plt.ylabel('')
    plt.title('')
    plt.xticks([])
    plt.yticks([])
    # for spine in plt.gca().spines.values():
    #     spine.set_visible(False)

    # Save the plot as an image
    graph_path = "graph.png"
    plt.savefig(graph_path)
    plt.close()

    # Open with Pillow
    img = Image.open(graph_path)


    return img


try:
    main()
except KeyboardInterrupt:
    print("Ctrl-C Entered")
    from waveshare_epd import epd7in5_V2 as disp
    disp.epdconfig.module_exit()
    sys.exit()