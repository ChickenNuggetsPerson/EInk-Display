import socket
import json
import os
import re
from datetime import datetime
from pathlib import Path

# Receiver address
REMOTE_HOST = "192.168.51.237"
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
cover_art_data = bytearray()
received_picture = False

ART_DIR = Path("/tmp/shairport-art")
ART_DIR.mkdir(parents=True, exist_ok=True)

def reset_metadata():
    global metadata, cover_art_data, received_picture
    metadata = {}
    cover_art_data = bytearray()
    received_picture = False

def handle_text_packet(text):
    for line in text.splitlines():
        if line.startswith("ssncmden"):
            # End of metadata — save and send
            image_file = save_cover_art() if received_picture else None
            if image_file:
                metadata["cover_art_file"] = str(image_file)

            if all(k in metadata for k in ("title", "artist", "album")):
                send_metadata(metadata)

            reset_metadata()

        for prefix, key in FIELD_MAP.items():
            if line.startswith(prefix):
                metadata[key] = line[len(prefix):].strip()

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
    try:
        cover_path = data.get("cover_art_file")
        image_data = b''
        if cover_path and os.path.exists(cover_path):
            with open(cover_path, 'rb') as f:
                image_data = f.read()

        # Remove local image path (optional)
        data["cover_art_file"] = os.path.basename(cover_path) if cover_path else None

        json_payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        json_len = struct.pack('>I', len(json_payload))  # 4-byte big endian

        with socket.create_connection((REMOTE_HOST, REMOTE_PORT), timeout=2) as sock:
            sock.sendall(json_len)
            sock.sendall(json_payload)
            sock.sendall(image_data)

        print(f"Sent metadata to {REMOTE_HOST}:{REMOTE_PORT}")
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
