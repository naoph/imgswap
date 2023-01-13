#! /usr/bin/env python3

import argparse
import hashlib
import json
import os
import requests
import sys
import time

import magic
from bs4 import BeautifulSoup

EXTMAP = {
    "img": {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "image/webp": "webp",
        "image/avif": "avif",
    },
    "video": {
        "video/mp4": "mp4",
        "video/webm": "webm",
    },
    "audio": {
        "audio/ogg": "ogg",
        "audio/flac": "flac",
        "audio/mpeg": "mp3",
    },
}

class Media:
    def __init__(self, path):
        self.path = os.path.realpath(path)
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        elif os.path.isdir(self.path):
            pass
        else:
            sys.exit("Specified media directory is not a directory")

        self.qty_known, self.qty_fetch, self.qty_fail = 0, 0, 0

        known_path = os.path.join(self.path, "known.json")
        if os.path.exists(known_path):
            with open(known_path, "rb") as kp:
                self.known = json.load(kp)
        else:
            self.known = {}

    def __repr__(self):
        return "Media({})".format(repr(self.path))

    """Return the local filename coresponding to a URL, downloading first if applicable"""
    def process(self, kind: str, url: str) -> str | None:
        if url in self.known:
            self.qty_known += 1
            print("{}: from known".format(self.known[url]))
            return self.known[url]

        time.sleep(0.25)
        try:
            response = requests.get(url)
        except:
            self.qty_fail += 1
            print("Error downloading {}".format(url))
            self.known[url] = None
            return None
        if not response.ok:
            self.qty_fail += 1
            self.known[url] = None
            return None

        mime = magic.from_buffer(response.content, mime=True)
        if mime in EXTMAP[kind]:
            extension = EXTMAP[kind][mime]
        else:
            self.qty_fail += 1
            self.known[url] = None
            return None

        sha = hashlib.sha256(response.content).hexdigest()
        filename = "{}.{}".format(sha, extension)
        open(os.path.join(self.path, filename), "wb").write(response.content)
        self.known[url] = filename
        print("{}: from remote".format(filename))
        self.qty_fetch += 1
        return filename

    """Save known URLs to disk"""
    def save_known(self):
        known_file = os.path.join(self.path, "known.json")
        dump = json.dumps(self.known)
        open(known_file, "w").write(dump)

parser = argparse.ArgumentParser()
parser.add_argument("infile", help="File to process")
parser.add_argument("outfile", help="Destination for processed file")
parser.add_argument("--media", required=False, help="Media directory")
args = parser.parse_args()

# Add default media directory based on `outfile`
if args.media is None:
    parent = os.path.dirname(os.path.realpath(args.outfile))
    args.media = os.path.join(parent, "imgswap_media")

media = Media(args.media)

# Load `infile`
with open(args.infile, "rb") as infile:
    soup = BeautifulSoup(infile, features="lxml")

# Process each <img>
for elem in soup.find_all("img"):
    local = media.process("img", elem["src"])
    if local is None:
        continue
    elem["data-imgswap-src"] = elem["src"]
    elem["src"] = os.path.join("imgswap_media", local)

# Process each <video>
for elem in soup.find_all("video"):
    for source in elem.find_all("source"):
        local = media.process("video", source["src"])
        if local is None:
            continue
        source["data-imgswap-src"] = source["src"]
        source["src"] = os.path.join("imgswap_media", local)

# Process each <audio>
for elem in soup.find_all("audio"):
    for source in elem.find_all("source"):
        local = media.process("audio", source["src"])
        if local is None:
            continue
        source["data-imgswap-src"] = source["src"]
        source["src"] = os.path.join("imgswap_media", local)

media.save_known()

final_html = str(soup)
open(args.outfile, "w").write(final_html)
print("Wrote new document to {}".format(args.outfile))
print("{} new media fetched, {} duplicate media inserted, {} media inaccessable".format(media.qty_fetch, media.qty_known, media.qty_fail))
