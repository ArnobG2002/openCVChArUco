import cv2
import numpy as np
import raw
import os
import math
import shutil
camera_matrix = np.load('camera_matrix.npy')
dist_coeffs = np.load('dist_coeffs.npy')


PATH_TO_YOUR_PAIRED = './chaarAdhyay'
PATH_TO_YOUR_CROP = './UndistortAndCropThese'
image_files = [os.path.join(path, name) for path, subdirs, files in os.walk(PATH_TO_YOUR_PAIRED) for name in files if name=="300.nef"]
image_files.sort()  # Ensure files are in order
currentlyReading={"image_file":None, "image_no": None, "newly_added": False}



def _box_kernel(width):
    """Normalised 1D box of (possibly fractional) width, integrated per pixel."""
    half = width / 2
    r = math.ceil(half - 0.5)
    k = np.arange(-r, r + 1, dtype=float)
    w = np.clip(np.minimum(k + 0.5, half) - np.maximum(k - 0.5, -half), 0, None)
    return (w / w.sum()).reshape(-1, 1)
def downsample(render, W, H):
    """Map a render made with plan(K, W, H) onto the original W x H frame."""
    fx, fy, cx, cy = camera_matrix[0,0], camera_matrix[1,1], camera_matrix[0,2], camera_matrix[1,2]
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
    return cv2.warpAffine(filtered, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

def undistort():    
    for image_file in image_files:
        #print(cv2.imread(image_file).shape) # Load the image to ensure it exists

        image = raw.raw_to_npArray(image_file)
        undistorted_image = cv2.undistort(image, camera_matrix, dist_coeffs)
        print("UndistortAndCropThese/camShader"+image_file[image_file.index("\\")+1:])
        cv2.imwrite("UndistortAndCropThese/camShader"+image_file[image_file.index("\\")+1:-4]+".png", undistorted_image)
        

undistort()
if os.path.exists("./Colors/Downsampled"):
    shutil.rmtree('./Colors/Downsampled')
image_files = [os.path.join(path, name) for path, subdirs, files in os.walk("Colors") for name in files]
image_files.sort()  # Ensure files are in order
os.makedirs("./Colors/Downsampled", exist_ok=True)
for image_file in image_files:
    image=cv2.imread(image_file)
    #image1=image[round(image.shape[0]/2-camera_matrix[1,2]) : , round(image.shape[1]/2-camera_matrix[0,2]) : ]
    image1=downsample(image, 6034, 4012)
    print(image.shape, image1.shape)
    cv2.imwrite(os.path.join("./Colors/Downsampled", os.path.basename(image_file)), image1)

# image_files = [os.path.join(path, name) for path, subdirs, files in os.walk(PATH_TO_YOUR_CROP) for name in files if name.endswith("_1.png")]
# image_files.sort()  # Ensure files are in order

# for image_file in image_files: 
#     print("Processing:", image_file)
#     image = cv2.imread(image_file)
#     hsv=cv2.cvtColor(image,cv2.COLOR_BGR2HSV)

#     # Define lower and uppper limits of what we call "brown"
#     brown_lo=np.array([0,0,0])
#     brown_hi=np.array([1, 1, 1])

#     # Mask image to only select browns
#     mask=cv2.inRange(hsv,brown_lo,brown_hi)

#     # Change image to red where we found brown
#     image[mask>0]=(255,255,255)

#     cv2.imwrite(image_file[:-4]+"_white.png",image)
#     print("Saved white image:", image_file[:-4]+"_white.png")

#     image1=cv2.imread(image_file[:image_file.rindex("\\")]+"\\0_1.png")
#     image1[mask>0]=(255,255,255)
#     cv2.imwrite(image_file[:image_file.rindex("\\")]+"\\0_1_white.png",image1)
#     image2=cv2.absdiff(image1, image)
#     cv2.imwrite(image_file[:image_file.rindex("\\")]+"\\0_1_diff.png",image2)