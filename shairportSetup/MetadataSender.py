#!/usr/bin/env python3

import socket
import json
import os
import struct
from pathlib import Path
import time

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

COVER_ART_DIR = Path("/tmp/shairport-sync/.cache/coverart")

last_sent_metadata = {}


def wait_for_image_stability(path: Path, timeout=2.0, interval=0.1):
    start_time = time.time()
    last_size = -1

    while time.time() - start_time < timeout:
        if not path.exists():
            time.sleep(interval)
            continue

        current_size = path.stat().st_size
        if current_size == last_size and current_size > 0:
            return True  # Stable and non-empty

        last_size = current_size
        time.sleep(interval)

    print("[!] Timeout waiting for image to stabilize")
    return False


def get_cover_art_path():
    try:
        files = list(COVER_ART_DIR.glob("*"))
        return files[0] if files else None
    except Exception as e:
        print(f"[!] Error accessing cover art directory: {e}")
        return None

def handle_text_packet(text):
    metadata = {}

    for line in text.splitlines():
        if line.startswith("ssncmden"):
            break  # End of metadata group
        for prefix, key in FIELD_MAP.items():
            if line.startswith(prefix):
                metadata[key] = line[len(prefix):].strip()

    if all(k in metadata for k in ("title", "artist", "album")):
        send_metadata(metadata)

def send_metadata(metadata):
    global last_sent_metadata

    minimal = {k: metadata.get(k) for k in ("title", "artist", "album")}
    if minimal == last_sent_metadata:
        print("Duplicate metadata — skipping send")
        return

    last_sent_metadata = minimal.copy()

    cover_path = get_cover_art_path()
    image_data = b''

    if cover_path:
        if wait_for_image_stability(cover_path):
            metadata["cover_art_file"] = cover_path.name
            with open(cover_path, 'rb') as f:
                image_data = f.read()
        else:
            metadata["cover_art_file"] = None
    else:
        metadata["cover_art_file"] = None

    try:
        json_payload = json.dumps(metadata, ensure_ascii=False).encode('utf-8')
        json_len = struct.pack('>I', len(json_payload))

        with socket.create_connection((REMOTE_HOST, REMOTE_PORT), timeout=2) as sock:
            sock.sendall(json_len)
            sock.sendall(json_payload)
            sock.sendall(image_data)

        print(f"Sent metadata to {REMOTE_HOST}:{REMOTE_PORT} - {metadata['title']}")
    except Exception as e:
        print(f"[!] Failed to send metadata: {e}")


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"Listening on UDP port {UDP_PORT}...")

    while True:
        data, _ = sock.recvfrom(65535)

        try:
            text = data.decode("utf-8")
            handle_text_packet(text)
        except UnicodeDecodeError:
            pass  # Ignore binary packets

if __name__ == "__main__":
    main()
