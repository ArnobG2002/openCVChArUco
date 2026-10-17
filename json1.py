import json
import os
import math
import raw
import argparse


import cv2
import numpy as np
PATH_TO_YOUR_IMAGES = './calibration_images'
PATH_TO_YOUR_COLORS = './Colors'
PATH_TO_YOUR_PAIRED = './pairedImages'
PATH_TO_FOUR= './chaarAdhyay'

#!/usr/bin/env python3
"""
Square-pixel, centred-principal-point render setup for an intrinsic matrix K
with fx != fy and an off-centre principal point.

The render uses f = max(fx, fy), so mapping it back onto the original image
only ever downsamples (the axis with the smaller focal length).

Conventions: OpenCV's, where pixel i has its centre at coordinate i. The
renderer is assumed to use a symmetric frustum, so its principal point is the
geometric canvas centre ((Wc - 1)/2, (Hc - 1)/2) in that convention.
Distortion is ignored and K must have zero skew.

Usage:
  plan only:        --K ... --width W --height H
  plan + downsample: add --render rendered.png --out result.png
"""



def _intrinsics(K):
    K = np.asarray(K, dtype=float)
    if abs(K[0, 1]) > 1e-9:
        raise ValueError("K has non-zero skew; this model cannot represent it.")
    return K[0, 0], K[1, 1], K[0, 2], K[1, 2]


def plan(K, W, H):
    fx, fy, cx, cy = _intrinsics(K)
    f = max(fx, fy)
    sx, sy = f / fx, f / fy  # original pixels -> square pixels (both >= 1)

    # Frame edges lie at -0.5 and W - 0.5, so the extents from the principal
    # point are cx + 0.5 and W - 0.5 - cx.
    Wc = 2 * math.ceil(sx * max(cx + 0.5, W - 0.5 - cx))
    Hc = 2 * math.ceil(sy * max(cy + 0.5, H - 0.5 - cy))

    fovy = 2 * math.degrees(math.atan((Hc / 2) / f))

    return {
        "render_resolution": [Wc, Hc],
        "fovy_deg": fovy,
    }


def _box_kernel(width):
    """Normalised 1D box of (possibly fractional) width, integrated per pixel."""
    half = width / 2
    r = math.ceil(half - 0.5)
    k = np.arange(-r, r + 1, dtype=float)
    w = np.clip(np.minimum(k + 0.5, half) - np.maximum(k - 0.5, -half), 0, None)
    return (w / w.sum()).reshape(-1, 1)


def downsample(render, K, W, H):
    """Map a render made with plan(K, W, H) onto the original W x H frame."""
    fx, fy, cx, cy = _intrinsics(K)
    f = max(fx, fy)
    Hc, Wc = render.shape[:2]
    cxr, cyr = (Wc - 1) / 2, (Hc - 1) / 2

    # Area prefilter: each output pixel covers f/fx render pixels horizontally
    # and f/fy vertically, so average over a box of that size before sampling.
    kx, ky = _box_kernel(f / fx), _box_kernel(f / fy)
    filtered = cv2.sepFilter2D(render, -1, kx, ky, borderType=cv2.BORDER_REPLICATE)

    # render -> original, from u = fx*x + cx and u_r = f*x + cxr.
    M = np.array([[fx / f, 0.0, cx - fx / f * cxr],
                  [0.0, fy / f, cy - fy / f * cyr]])
    return cv2.warpAffine(filtered, M, (W, H), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_REPLICATE)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--K", required=True,
                    help="3x3 intrinsic matrix as JSON, e.g. '[[fx,0,cx],[0,fy,cy],[0,0,1]]'")
    ap.add_argument("--width", type=int, required=True, help="original image width W")
    ap.add_argument("--height", type=int, required=True, help="original image height H")
    ap.add_argument("--render", help="rendered image at render_resolution to downsample")
    ap.add_argument("--out", help="output path for the downsampled W x H image")
    a = ap.parse_args()

    K = json.loads(a.K)
    p = plan(K, a.width, a.height)

    if a.render or a.out:
        if not (a.render and a.out):
            ap.error("--render and --out must be given together")
        img = cv2.imread(a.render, cv2.IMREAD_UNCHANGED)
        if img is None:
            ap.error(f"could not read {a.render}")
        if [img.shape[1], img.shape[0]] != p["render_resolution"]:
            ap.error(f"render is {img.shape[1]}x{img.shape[0]}, "
                     f"expected {p['render_resolution'][0]}x{p['render_resolution'][1]}")
        cv2.imwrite(a.out, downsample(img, K, a.width, a.height))

    print(json.dumps(p, indent=2))


if __name__ == "__main__":
    main()
def getImageFiles(calibrate):
    # Load PNG images from folder
    if(calibrate=="images"):
        image_files = [os.path.join(PATH_TO_YOUR_IMAGES, f) for f in os.listdir(PATH_TO_YOUR_IMAGES) if f.endswith(".nef")]
    elif(calibrate=="colors"):
        image_files = [os.path.join(path, name) for path, subdirs, files in os.walk(PATH_TO_YOUR_COLORS) for name in files]
    elif(calibrate=="paired"):
        image_files = [os.path.join(path, name) for path, subdirs, files in os.walk(PATH_TO_YOUR_PAIRED) for name in files if name.endswith("_0.nef")]
    elif(calibrate=="ela"):
        image_files = [os.path.join(path, name) for path, subdirs, files in os.walk(PATH_TO_FOUR) for name in files if name=='250.nef']
    image_files.sort()  # Ensure files are in order
    return image_files
def writeUpLookatEye( camera_matrix, calibrate, i, matrix):
    image_files = getImageFiles(calibrate)
    #print("writing", i, "matrix")
    image = raw.raw_to_npArray(image_files[i])
    with open('CameraShaders/camShader.json', 'r') as openfile:
        # Reading from json file
        json_object = json.load(openfile)
    #print(json_object)
    fx, fy, cx, cy = camera_matrix[0,0], camera_matrix[1,1], camera_matrix[0,2], camera_matrix[1,2]
    f = max(fx, fy)
    sx, sy = f / fx, f / fy  # original pixels -> square pixels (both >= 1)

    # Frame edges lie at -0.5 and W - 0.5, so the extents from the principal
    # point are cx + 0.5 and W - 0.5 - cx.
    Wc = 2 * math.ceil(sx * max(cx + 0.5, image.shape[1] - 0.5 - cx))
    Hc = 2 * math.ceil(sy * max(cy + 0.5, image.shape[0] - 0.5 - cy))
    json_object['Data']['Res'] = [Wc, Hc] #[2*round(max(camera_matrix[0,2], image.shape[1]-camera_matrix[0,2])), 2*round(max(camera_matrix[1,2], image.shape[0]-camera_matrix[1,2]))]
    
    json_object['Data']['Up'] = matrix[:, 0].tolist()
    json_object['Data']['Lookat'] = matrix[:, 1].tolist()
    json_object['Data']['Eye'] = matrix[:, 2].tolist()
    json_object['Data']['FovY']= 2 * math.degrees(math.atan((Hc / 2) / f)) #round(math.degrees(2 * math.atan(json_object['Data']['Res'][1] / (2 * camera_matrix[1,1]))))
    if calibrate=="paired":
        json_object['Data']['Name']= image_files[i][len(PATH_TO_YOUR_PAIRED+"/"):image_files[i].rfind("\\")]
    elif calibrate=="ela":
        json_object['Data']['Name']= image_files[i][len(PATH_TO_FOUR+"/"):image_files[i].rfind("\\")]
    else:
        json_object['Data']['Name']= image_files[i][len(PATH_TO_YOUR_IMAGES+"/"):-4]
    #print(json_object)
    with open('CameraShaders/camShader'+json_object['Data']['Name']+'.json', 'w') as outfile:
        # Writing to json file
        json.dump(json_object, outfile, indent=4)
    with open('JsonStructure.json', 'r') as openfile:
        # Reading from json file
        json_object1 = json.load(openfile)
        json_object1['cameraConfig'].append('Default\\CameraShaders\\camShader'+json_object['Data']['Name']+'.json')
    with open('JsonStructure.json', 'w') as outfile:
        # Writing to json file
        json.dump(json_object1, outfile, indent=4)

def writeDistortion(l1):
    #print("writing", i, "matrix")
    with open('CameraShaders/camShader.json', 'r') as openfile:
        # Reading from json file
        json_object = json.load(openfile)
    #print(json_object)
    #json_object['Data']['radialDistCoeff'] = [l1[0], l1[1], l1[-1]]
    #json_object['Data']['tangDistCoeff'] = [l1[2], l1[3]]
    json_object['Data']['radialDistCoeff'] = [0, 0, 0]
    json_object['Data']['tangDistCoeff'] = [0, 0, 0]
    #print(json_object)
    with open('CameraShaders/camShader'+'.json', 'w') as outfile:
        # Writing to json file
        json.dump(json_object, outfile, indent=4)
    with open('JsonStructure.json', 'r') as openfile:
        # Reading from json file
        json_object1 = json.load(openfile)
        json_object1['cameraConfig']=[]
    with open('JsonStructure.json', 'w') as outfile:
        # Writing to json file
        json.dump(json_object1, outfile, indent=4)