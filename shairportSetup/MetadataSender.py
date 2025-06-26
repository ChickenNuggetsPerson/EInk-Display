#!/usr/bin/env python3

import socket
import json
import os
import re
from datetime import datetime
from pathlib import Path

# Receiver address
REMOTE_HOST = "192.168.51.237"
# REMOTE_HOST = "192.168.51.24"
REMOTE_PORT = 6000

UDP_IP = "0.0.0.0"
UDP_PORT = 5555

FIELD_MAP = {
    "coreasal": "album",
    "coreasar": "artist",
    "coreascp": "composer",
    "coreasgn": "genre",
    "coreminm": "title",
    "coreastm": "duration",
}

metadata = {}
last_sent_metadata = {}

cover_art_data = bytearray()
received_picture = False

ART_DIR = Path("/tmp/shairport-art")
ART_DIR.mkdir(parents=True, exist_ok=True)

import threading
send_timer = None

def reset_metadata():
    global metadata, cover_art_data, received_picture
    metadata = {}
    cover_art_data = bytearray()
    received_picture = False

def handle_text_packet(text):
    global metadata, send_timer

    lines = text.splitlines()
    saw_end = False

    for line in lines:
        if line.startswith("ssncmden"):
            saw_end = True
        else:
            for prefix, key in FIELD_MAP.items():
                if line.startswith(prefix):
                    metadata[key] = line[len(prefix):].strip()

    if saw_end:
        # Cancel previous timer if still waiting
        if send_timer and send_timer.is_alive():
            send_timer.cancel()

        # Delay sending to give image time to arrive
        send_timer = threading.Timer(0.5, delayed_send)
        send_timer.start()

def delayed_send():
    image_file = save_cover_art() if received_picture else None
    if image_file:
        metadata["cover_art_file"] = str(image_file)

    if all(k in metadata for k in ("title", "artist", "album")):
        send_metadata(metadata)

    reset_metadata()


def handle_binary_packet(data):
    global received_picture, cover_art_data
    if b"ssncPICT" in data:
        offset = data.find(b"ssncPICT") + len(b"ssncPICT")
        chunk = data[offset:]
        cover_art_data.extend(chunk)
        received_picture = True

def save_cover_art():
    if not cover_art_data:
        return None
    filename = ART_DIR / f"cover.jpg"
    with open(filename, 'wb') as f:
        f.write(cover_art_data)
    return filename

import struct
def send_metadata(data):
    global last_sent_metadata

    if not data.get("cover_art_file"): # Only send if we have cover art
        return

    # Skip duplicate metadata
    minimal = {k: data.get(k) for k in ("title", "artist", "album")}
    if minimal == last_sent_metadata:
        print("Duplicate metadata — skipping send")
        return

    last_sent_metadata = minimal.copy()

    try:
        cover_path = data.get("cover_art_file")
        image_data = b''
        if cover_path and os.path.exists(cover_path):
            # with open(cover_path, 'rb') as f:
            #     image_data = f.read()
            pass # TODO: Figure out how to wait for image to fully load in

        # Clean up the payload for transmission
        data["cover_art_file"] = os.path.basename(cover_path) if cover_path else None

        json_payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        json_len = struct.pack('>I', len(json_payload))

        with socket.create_connection((REMOTE_HOST, REMOTE_PORT), timeout=2) as sock:
            sock.sendall(json_len)
            sock.sendall(json_payload)
            sock.sendall(image_data)

        title = metadata["title"]
        print(f"Sent metadata to {REMOTE_HOST}:{REMOTE_PORT} - {title}")
    except Exception as e:
        print(f"[!] Failed to send metadata: {e}")


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"Listening on UDP port {UDP_PORT}...")

    while True:
        data, addr = sock.recvfrom(65535)

        try:
            text = data.decode("utf-8")
            handle_text_packet(text)
        except UnicodeDecodeError:
            handle_binary_packet(data)

if __name__ == "__main__":
    main()
