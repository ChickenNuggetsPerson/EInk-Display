#!/usr/bin/env python3

import os
import sys
import json
import base64
import uuid
import imghdr
import xml.etree.ElementTree as ET

PIPE_PATH = '/tmp/shairport-sync-metadata'

def parse_item_xml(item_xml):
    """
    Parse a single <item>...</item> XML string and return a dict with fields:
    type_code (str), code_code (str), data (bytes or None).
    """
    try:
        elem = ET.fromstring(item_xml)
    except ET.ParseError:
        return None
    # Extract hex strings
    type_str = elem.findtext('type') or ''
    code_str = elem.findtext('code') or ''
    length = elem.findtext('length')  # we may not need it explicitly
    # Convert hex to integer
    try:
        type_int = int(type_str, 16)
    except ValueError:
        return None
    try:
        code_int = int(code_str, 16)
    except ValueError:
        return None
    # Convert to 4-char ASCII codes
    try:
        type_code = type_int.to_bytes(4, 'big').decode('ascii')
    except Exception:
        type_code = ''
    try:
        code_code = code_int.to_bytes(4, 'big').decode('ascii')
    except Exception:
        code_code = ''
    # If not exactly 'ssnc', treat as core metadata
    if type_code != 'ssnc':
        type_code = 'core'
    # Extract data payload (base64)
    data_elem = elem.find('data')
    data_bytes = b''
    if data_elem is not None and data_elem.text:
        try:
            data_bytes = base64.b64decode(data_elem.text)
        except Exception:
            data_bytes = b''
    return {
        'type': type_code,
        'code': code_code,
        'data': data_bytes
    }

def save_cover_image(data_bytes):
    """
    Save image bytes to a temporary file in /tmp and return the file path.
    """
    if not data_bytes:
        return ''
    # Guess image format
    img_type = imghdr.what(None, data_bytes)
    if img_type == 'jpeg':
        ext = 'jpg'
    elif img_type == 'png':
        ext = 'png'
    else:
        # default to jpg if unknown
        ext = 'jpg'
    # Use UUID to create a unique filename
    filename = f"/tmp/shairport_cover_{uuid.uuid4().hex}.{ext}"
    try:
        with open(filename, 'wb') as imgf:
            imgf.write(data_bytes)
    except Exception as e:
        # If writing fails, print error and return empty
        print(f"Error writing cover image: {e}", file=sys.stderr)
        return ''
    return filename

def main():
    # Open the Shairport Sync metadata pipe for reading
    if not os.path.exists(PIPE_PATH):
        print(f"Metadata pipe {PIPE_PATH} does not exist.", file=sys.stderr)
        return
    try:
        with open(PIPE_PATH, 'r') as pipe:
            item_buffer = None
            metadata = None
            for line in pipe:
                # Start of a new <item>
                if '<item>' in line:
                    item_buffer = line.strip('\n')
                elif item_buffer is not None:
                    item_buffer += line.strip('\n')
                else:
                    continue

                # If we reach end of item, parse it
                if '</item>' in line and item_buffer is not None:
                    item_data = parse_item_xml(item_buffer)
                    item_buffer = None
                    print(f"[DEBUG] Received item: type={item_data['type']}, code={item_data['code']}", file=sys.stderr)

                    if item_data is None:
                        print(f"[DEBUG] Received item: type={item_data['type']}, code={item_data['code']}", file=sys.stderr)
                        continue

                    type_code = item_data['type']
                    code_code = item_data['code']
                    data_bytes = item_data['data']

                    # Handle metadata bundle start
                    if type_code == 'ssnc' and code_code == 'mdst':
                        # Initialize a new metadata record
                        metadata = {"title": "", "artist": "", "album": "", "cover": ""}
                    # If we see metadata end, output JSON
                    elif type_code == 'ssnc' and code_code == 'mden':
                        if metadata is not None:
                            print(json.dumps(metadata))
                        metadata = None
                    # Core metadata items (title/artist/album)
                    elif type_code == 'core' and metadata is not None:
                        # Decode text (UTF-8) from the data bytes
                        try:
                            text = data_bytes.decode('utf-8', errors='replace')
                        except Exception:
                            text = ''
                        if code_code == 'asar':
                            metadata['artist'] = text
                        elif code_code == 'asal':
                            metadata['album'] = text
                        elif code_code == 'minm':
                            metadata['title'] = text
                    # Cover art image
                    elif type_code == 'ssnc' and code_code == 'PICT' and metadata is not None:
                        if data_bytes:
                            cover_path = save_cover_image(data_bytes)
                            if cover_path:
                                print(f"[DEBUG] Cover image saved to {cover_path}", file=sys.stderr)
                                metadata['cover'] = cover_path
                            else:
                                print("[DEBUG] Failed to save cover image", file=sys.stderr)
                        else:
                            print("[DEBUG] Received PICT with no data", file=sys.stderr)


    except Exception as e:
        print(f"Error reading metadata pipe: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
