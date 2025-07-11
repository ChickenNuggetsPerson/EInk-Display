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


import socket
import json
import struct
from datetime import datetime
from pathlib import Path
import traceback

HOST = "0.0.0.0"
PORT = 6000
IMAGE_SAVE_DIR = Path("./data/received_covers")
IMAGE_SAVE_DIR.mkdir(exist_ok=True)

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(1)
    print(f"Receiver listening on {PORT}...")

    while True:
        conn, addr = server.accept()
        with conn:
            print(f"Connection from {addr}")
            try:
                # Read 4 bytes for JSON length
                raw_len = conn.recv(4)
                if not raw_len or len(raw_len) != 4:
                    print("Invalid header length")
                    continue

                json_len = struct.unpack('>I', raw_len)[0]

                # Read JSON payload
                json_data = b''
                while len(json_data) < json_len:
                    chunk = conn.recv(json_len - len(json_data))
                    if not chunk:
                        break
                    json_data += chunk

                metadata = json.loads(json_data.decode('utf-8'))

                # Read image (remaining data)
                image_data = b''
                while True:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    image_data += chunk

                # Save image
                if metadata.get("cover_art_file") and image_data:
                    filename = IMAGE_SAVE_DIR / f"cover.jpg"
                    with open(filename, 'wb') as f:
                        f.write(image_data)
                    metadata["cover_art_file"] = str(filename)
                    print(f"Saved cover art: {filename}")
                else:
                    print(" No image included.")

                print(metadata["title"])
                display(metadata)

            except Exception as e:
                print(f"[!] Error: {e}")
                traceback.print_exc()


def clipText(text: str, maxChars):
    if (len(text) > maxChars):
        return text[0:(maxChars - 3)] + "..."
    return text

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
        strs[len(strs) - 1] = line[0:-3] + "..."

    return strs


def genImage(metadata):

    width = 800
    height = 480

    Himage = Image.new('1', (width, height), 255)
    draw = ImageDraw.Draw(Himage)

    rightSideWidth = int(width/2)
    rightLeadingStart = width - rightSideWidth
    rightSideCenter = int(rightSideWidth / 2) + rightLeadingStart

    draw.text((rightSideCenter, 50), "Now Playing:", "black", Smono, anchor="mb")

    titleTexts = wrapText(metadata["title"], 24, 4)
    for i, line in enumerate(titleTexts):
        draw.text((rightSideCenter, 230 - ((len(titleTexts) - 1) - i) * 40 ), line, "black", Sfont, anchor="mb")
    
    for i, line in enumerate(wrapText(metadata["artist"], 24, 5)):
        draw.text((rightSideCenter, 280 + (i * 30)), line, "black", Mmono, anchor="mb")


    coverPadding = 20
    coverSize = 370
    radius = 15

    mask = Image.new('L', (coverSize, coverSize), 0)
    maskDraw = ImageDraw.Draw(mask)
    maskDraw.rounded_rectangle((0, 0, coverSize, coverSize), radius=radius, fill=255) 

    cover = Image.open("./data/received_covers/cover.jpg")
    cover = cover.resize((coverSize, coverSize), resample=Image.Resampling.NEAREST)
    cover = cover.convert("1")
    Himage.paste(cover, (coverPadding, int(height / 2) - int(coverSize / 2)), mask)


    return Himage

def display(metadata):
    image = genImage(metadata)
    image.save("./data/music.png")
    subprocess.run(["python3", "display.py", "./data/music.png"]) # Run the main script


if __name__ == "__main__":
    main()
