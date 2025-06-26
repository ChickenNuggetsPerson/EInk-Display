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


import socket
import json
import struct
from datetime import datetime
from pathlib import Path

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

                print("Metadata:")
                print(json.dumps(metadata, indent=2))
                display(metadata)

            except Exception as e:
                print(f"[!] Error: {e}")


def genImage(metadata):

    width = 100
    height = 100

    Himage = Image.new('1', (width, height), 255)
    draw = ImageDraw.Draw(Himage)

    draw.text((10, 10), metadata["title"], "black", Sfont, anchor="lt")

    return Himage

def display(metadata):
    load_dotenv()  # Load environment variables from .env

    image = genImage(metadata)

    if (platform.system() == "Darwin"):

        image = image.save("out.jpg")

    else:
        try:
            from waveshare_epd import epd7in5_V2 as disp
            epd = disp.EPD()
            epd.init_part()
            epd.display_Partial(epd.getbuffer(image), 0, 0, image.width, image.height)
            epd.sleep()
            print("Image Displayed")
        except Exception as e:
            print(f"Error: {e}")
            from waveshare_epd import epd7in5_V2 as disp
            disp.epdconfig.module_exit()
            sys.exit()


if __name__ == "__main__":
    main()
