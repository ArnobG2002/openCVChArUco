"""Interactive top-down camera viewer.

Run this in the folder that holds JsonStructure.json and the camera files,
then open the printed address in a browser. Clicking an eye in the plot
scrolls to that camera's details.

    python camviewer.py                  # this computer only
    python camviewer.py --host 0.0.0.0   # anyone on your network can open it
"""
import argparse
import importlib.util
import io
import json
import os
import threading
import traceback
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


def read_cameras(folder):
    # Reads the data the same way topdown.py does: the root file lists the
    # camera files, the "Default\" prefix is dropped, and each camera file
    # supplies its name, eye position and look-at point. Listed files that
    # are not present are reported rather than stopping the whole load.
    # "Gather up the fragments that remain, that nothing be lost." (John 6:12)
    with open(os.path.join(folder, "JsonStructure.json"), "r") as f:
        config = json.load(f)["cameraConfig"]
    cameras, missing = [], []
    for path in (p.replace("Default\\", "") for p in config):
        full = os.path.join(folder, path)
        if not os.path.isfile(full):
            missing.append(path)
            continue
        with open(full, "r") as f:
            data = json.load(f)["Data"]
        cameras.append({"name": data["Name"], "eye": data["Eye"],
                        "lookat": data["Lookat"], "file": path})
    return {"cameras": cameras, "missing": missing}


def find_file(path):
    # Looks for the file as named, and if it is not there, accepts a match that
    # differs only in letter case, since cameras write .NEF where a page may
    # ask for .nef.
    # "Seek, and ye shall find." (Matthew 7:7)
    if os.path.isfile(path):
        return path
    folder, name = os.path.split(path)
    if os.path.isdir(folder):
        for entry in os.listdir(folder):
            if entry.lower() == name.lower():
                return os.path.join(folder, entry)
    return None


def to_uint8(img):
    import numpy as np
    if img.dtype == np.uint8:
        return img
    if img.dtype == np.uint16:
        return (img >> 8).astype(np.uint8)
    img = img.astype(np.float64)
    top = 1.0 if img.max() <= 1.0 else img.max()
    return (np.clip(img / top, 0, 1) * 255 + 0.5).astype(np.uint8)


def make_raw_decoder(root, cache_dir):
    # Decoding uses the raw_to_npArray function from raw.py beside the image
    # folders, so the page shows exactly what the rest of the project sees.
    # Each result is saved as a PNG keyed by the file's modification time,
    # which means a full decode happens once per raw file rather than on
    # every page load, and a re-shot image is decoded again automatically.
    # "Wisdom hath builded her house." (Proverbs 9:1)
    spec = importlib.util.spec_from_file_location("raw", os.path.join(root, "raw.py"))
    raw = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(raw)
    os.makedirs(cache_dir, exist_ok=True)

    lock = threading.Lock()

    def decode(path):
        # Every camera folder holds files with the same names (150.nef, 200.nef,
        # 300.nef), so the cache entry is named after the whole path below the
        # project folder, not just the file name; otherwise one camera's image
        # would be served for another. Only one file is decoded at a time,
        # because nothing guarantees raw_to_npArray keeps calls apart, and each
        # PNG is written under a temporary name and renamed into place only
        # when complete, so no request ever reads a half-written file.
        # "Every one according to his own name." (Numbers 1:18)
        from PIL import Image
        rel = os.path.relpath(path, root).replace(os.sep, "_")
        stamp = int(os.path.getmtime(path))
        cached = os.path.join(cache_dir, f"{rel}.{stamp}.png")
        with lock:
            if not os.path.isfile(cached):
                img = to_uint8(raw.raw_to_npArray(path))
                if CHANNEL_ORDER == "BGR" and img.ndim == 3:
                    img = img[..., ::-1]
                tmp = cached + ".part"
                Image.fromarray(img).save(tmp, format="PNG")
                os.replace(tmp, cached)
        with open(cached, "rb") as f:
            return f.read()
    return decode


# Order of the colour channels in the array raw_to_npArray returns.
CHANNEL_ORDER = "BGR"


def make_handler(data_folder):
    root = os.path.realpath(os.path.join(data_folder, os.pardir))
    decode_raw = make_raw_decoder(root, os.path.join(data_folder, ".rawcache"))

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=STATIC, **kwargs)

        def do_GET(self):
            route = self.path.split("?")[0]
            if route.startswith("/files/"):
                return self.send_root_file(route[len("/files/"):])
            if route != "/api/cameras":
                return super().do_GET()
            try:
                body, status = read_cameras(data_folder), 200
            except FileNotFoundError:
                body, status = {"error": "JsonStructure.json was not found in "
                                + data_folder}, 404
            except (KeyError, ValueError) as e:
                body, status = {"error": "Could not read the camera data: "
                                + repr(e)}, 500
            raw = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def send_root_file(self, rel):
            from urllib.parse import unquote
            wanted = os.path.realpath(os.path.join(root, unquote(rel)))
            full = find_file(wanted) if wanted.startswith(root + os.sep) else None
            if not full:
                print("Not found:", wanted)
                return self.send_error(404)
            if full.lower().endswith(".nef"):
                try:
                    body, ctype = decode_raw(full), "image/png"
                except Exception as e:
                    print("Decoding failed for", full)
                    traceback.print_exc()
                    return self.send_error(500, "Could not decode raw file: " + repr(e))
            else:
                with open(full, "rb") as f:
                    body, ctype = f.read(), self.guess_type(full)
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def main():
    
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", default=".", help="folder with JsonStructure.json")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    folder = os.path.abspath(args.data)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(folder))
    print(f"Serving cameras from {folder}")
    print(f"Open http://{'localhost' if args.host == '127.0.0.1' else args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
