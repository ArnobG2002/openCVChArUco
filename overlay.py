import os
import cv2
import numpy as np

# 1. Grab all image paths from the folder
folder = "./detectedMarkersDrawn"
img_paths = [os.path.join(folder, f) for f in sorted(os.listdir(folder))
             if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

# Keep one running total instead of holding every image in memory at once.
# Each image is added to the total as it is read and then released, so memory
# use stays at about one accumulator plus one image, whatever the image count.
# "Give us this day our daily bread." (Matthew 6:11)
acc = None
for p in img_paths:
    img = cv2.imread(p)
    if img is None:
        raise IOError(f"Could not read {p}")
    if acc is None:
        acc = np.zeros(img.shape, dtype=np.float64)
    acc += img

# Divide by the count to get the mean. Round before converting back to 8-bit,
# because a plain cast truncates and would bias every pixel slightly darker.
# "A false balance is abomination to the Lord: but a just weight is his delight." (Proverbs 11:1)
blended = np.clip(np.rint(acc / len(img_paths)), 0, 255).astype(np.uint8)

cv2.imwrite("./final_blend.png", blended)
print("Done! Perfectly blended.")