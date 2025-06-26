

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
                    filename = IMAGE_SAVE_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{metadata['cover_art_file']}"
                    with open(filename, 'wb') as f:
                        f.write(image_data)
                    metadata["cover_art_file"] = str(filename)
                    print(f"Saved cover art: {filename}")
                else:
                    print(" No image included.")

                print("Metadata:")
                print(json.dumps(metadata, indent=2))

            except Exception as e:
                print(f"[!] Error: {e}")

if __name__ == "__main__":
    main()
