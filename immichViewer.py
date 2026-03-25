#!/usr/bin/env python3

import subprocess
import sys
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
Mmono = ImageFont.truetype('./SourceCodePro-VariableFont_wght.ttf', 25, encoding="unic")
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
import random


import socket
import json
import struct
from datetime import datetime
from pathlib import Path
import traceback
import shutil


def main():
    load_dotenv()
    
    image = genImage()
    image.save("./data/immich.png")
    subprocess.run(["python3", "display.py", "./data/immich.png"])

def genImage():
    
    imagePath = getRandomImage()

    width = 800
    height = 480

    Himage = Image.new('1', (width, height), 255)

    cover = Image.open(imagePath)
    ratio = cover.size[1] / height
    
    newWidth = int(cover.size[0] / ratio) + 1
    newHeight = int(cover.size[1] / ratio) + 1
    
    cover = cover.resize((newWidth, newHeight), resample=Image.Resampling.NEAREST)
    cover = cover.convert("1")
    Himage.paste(cover, (int(width / 2 - newWidth / 2), 0))


    return Himage

def getRandomImage():
    
        
    # albums = callAPI("/api/albums")
    # for (i, a) in enumerate(albums):
    #     print(i, a["albumName"], "-", a['id'])
    
    albumId = os.getenv("IMMICH_ALBUM_ID")
    album = callAPI(f"/api/albums/{albumId}")
    
    assets = album["assets"]
    assetCount = len(assets)
    
    chosenIndex = int(random.random() * assetCount)
    chosenAsset = assets[chosenIndex]
    
    filename = chosenAsset['originalFileName']

    try:
        shutil.rmtree("./data/images")
    except Exception as e:
        print(e)
        # return ""
    
    os.mkdir("./data/images")
    
    download_immich_asset(chosenAsset["id"], f"./data/images/{filename}")
    return f"./data/images/{filename}"

def callAPI(path, parms={}):
    BASEURL = os.getenv("IMMICH_BASE_URL")
    APIKEY = os.getenv("IMMICH_API_KEY")
    
    headers = {
        "x-api-key": APIKEY,
        "Accept": "application/json",
    }
    
    response = requests.get(f"{BASEURL}{path}", headers=headers, params=parms, verify=False)
    return response.json()

def download_immich_asset(asset_id, save_path):
    
    BASEURL = os.getenv("IMMICH_BASE_URL")
    APIKEY = os.getenv("IMMICH_API_KEY")

    url = f"{BASEURL}/api/assets/{asset_id}/original"
    headers = {"x-api-key": APIKEY}

    print("Downloading Asset:", asset_id)

    try:
        with requests.get(url, headers=headers, stream=True, verify=False) as r:
            r.raise_for_status() 
            with open(save_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to download asset {asset_id}: {e}")
        return False


if __name__ == "__main__":
    main()
