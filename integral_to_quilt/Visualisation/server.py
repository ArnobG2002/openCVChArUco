"""
Hogel Ray Viewer — FastAPI server
Serves the HTML/JS frontend and provides the quilt-synthesis endpoint.

Usage:
    python server.py <path/to/integral_image.png> [--port 8000] [--host 127.0.0.1]

Then open:  http://127.0.0.1:8000/
"""
import os
import sys
import argparse

import cv2
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, RedirectResponse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, '..'))
from integral_to_quilt_v4 import integral_to_quilt


def build_app(image_path: str) -> FastAPI:
    app = FastAPI(title='Hogel Ray Viewer')

    # Allow direct file:// access and cross-origin dev setups
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_methods=['GET'],
        allow_headers=['*'],
    )

    @app.get('/')
    def root():
        return RedirectResponse('/hogel_rays.html')

    @app.get('/hogel_rays.html')
    def serve_html():
        return FileResponse(os.path.join(BASE_DIR, 'hogel_rays.html'))

    @app.get('/hogel_rays.js')
    def serve_js():
        return FileResponse(os.path.join(BASE_DIR, 'hogel_rays.js'))

    @app.get('/quilt')
    def get_quilt(
        z_cam: float = Query(..., description='Camera z in hogel-pitch units (negative = in front of display)'),
    ):
        if not os.path.isfile(image_path):
            raise HTTPException(status_code=404, detail=f'Image not found: {image_path}')

        quilt = integral_to_quilt(image_path, z_cam_hogels=z_cam)

        ok, buf = cv2.imencode('.png', quilt)
        if not ok:
            raise HTTPException(status_code=500, detail='Failed to encode quilt')

        return Response(content=bytes(buf), media_type='image/png')

    return app


if __name__ == '__main__':
    import uvicorn

    parser = argparse.ArgumentParser(description='Hogel Ray Viewer server')
    parser.add_argument('image_path', help='Path to HPO integral image')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--host', default='127.0.0.1')
    args = parser.parse_args()

    app = build_app(args.image_path)

    print(f'\n  Hogel Ray Viewer')
    print(f'  http://{args.host}:{args.port}/')
    print(f'  Image: {os.path.abspath(args.image_path)}\n')

    uvicorn.run(app, host=args.host, port=args.port)
