import sys
import json
import re

current_metadata = {}
last_sent_metadata = {}

in_bundle = False

field_re = re.compile(r'^(Title|Artist|Album Name):\s+"(.*?)"\.\s*$')
bundle_start_re = re.compile(r'^Metadata bundle ".*?" start\.$')
bundle_end_re = re.compile(r'^Metadata bundle ".*?" end\.$')

def reset_metadata():
    global current_metadata
    current_metadata = {
        "title": None,
        "artist": None,
        "album": None
    }

def maybe_output_metadata():
    if all(current_metadata.values()) and current_metadata != last_sent_metadata:
        print(json.dumps(current_metadata, ensure_ascii=False), flush=True)
        last_sent_metadata.update(current_metadata)

def parse_line(line):
    global in_bundle
    line = line.strip()

    if bundle_start_re.match(line):
        in_bundle = True
        reset_metadata()
        return

    if bundle_end_re.match(line):
        in_bundle = False
        maybe_output_metadata()
        return

    if not in_bundle:
        return

    match = field_re.match(line)
    if match:
        key, value = match.groups()
        if key == "Title":
            current_metadata["title"] = value
        elif key == "Artist":
            current_metadata["artist"] = value
        elif key == "Album Name":
            current_metadata["album"] = value

def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            continue
        parse_line(line)

if __name__ == "__main__":
    main()
