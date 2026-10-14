import numpy as np
import argparse
import json
import cv2

# ---------------------------------------------------------------------------
# Default parameters derived from the config JSON
# ---------------------------------------------------------------------------
_DEFAULTS = dict(
    num_hogels      = 819,
    directional_res = 81,
    display_fov_deg = 60.0,    # displayFOV[0]
    z_cam_hogels    = None,    # None → natural viewing distance (see above)
    flip_spatial_y  = False,
)


def integral_to_quilt(
    image_path     : str,
    num_hogels     : int   = _DEFAULTS["num_hogels"],
    directional_res: int   = _DEFAULTS["directional_res"],
    display_fov_deg: float = _DEFAULTS["display_fov_deg"],
    z_cam_hogels   : float = None,
    flip_spatial_y : bool  = False,
) -> np.array:
    """
    Parameters----------------------------------------------------------------------------------------------------
    ----------
    image_path      : path to HPO integral image
                      Width must equal num_hogels * directional_res
    num_hogels      : number of hogels (spatial positions) horizontally
    directional_res : number of directional views per hogel  (= D)
                        The term directional resolution (Dr) is often used to describe 
                        the number of views that a hogel microlens can project along one axis [Burnett].
    display_fov_deg : horizontal full-FOV of the light field in degrees
    z_cam_hogels    : virtual camera distance from display in hogel-pitch units.
                      None → natural viewing distance = num_hogels/(2*maxAngle)
    flip_spatial_y  : flip each tile vertically (use if output appears upside-down)

    Returns
    -------
    PIL Image — the quilt
        Width  = num_hogels * directional_res   (same as integral image)
        Height = integral image height
        Tile v occupies columns [v*num_hogels, (v+1)*num_hogels)
    """
    img_np = cv2.imread(image_path)
    H, W   = img_np.shape[:2]

    D = directional_res
    N = num_hogels

    expected_w = N * D
    if W != expected_w:
        raise ValueError(
            f"Width mismatch: expected {expected_w} ({N} hogels × {D} dirs), got {W}."
        )

    max_angle = np.tan(np.radians(display_fov_deg / 2.0))

    if z_cam_hogels is None:
        # Natural viewing distance: camera FOV == display directional FOV
        z_cam_hogels = -N / (1 * max_angle)

    display_center = (N - 1) / 2.0          # hogel-index of display centre

    # -----------------------------------------------------------------------
    # Perspective-correct view synthesis
    # -----------------------------------------------------------------------
    h_indices = np.arange(N, dtype=np.float64)
    # Pre-compute the per-hogel parallax offset (independent of v)
    parallax = (D - 1) * ((display_center - h_indices) / (2*z_cam_hogels * max_angle)+0.5)
    # Is there a way to find the 2 whole factors of an int that are closest together?
    # https://stackoverflow.com/questions/28328437/
    cols = int(np.floor(np.sqrt(D)))
    while D % cols != 0:
        cols += 1
    rows = D // cols

    # Canvas: cols tiles wide, rows tiles tall
    quilt_shape = (rows * H, cols * N) + img_np.shape[2:]
    quilt_np = np.zeros(quilt_shape, dtype=img_np.dtype)

    for v in range(D):
        dx_float = parallax + (0.5+N/(4*z_cam_hogels*max_angle))*(D-1-2*v) # (N,)
        dx_int   = np.clip(np.round(dx_float).astype(np.int32),
                                   0, D - 1)                             # (N,)
        
        # Integral image column for hogel h at direction dx_int[h]:
        #   col = h * D + dx_int[h]
        src_cols = (np.arange(N, dtype=np.int32) * D) + dx_int  # (N,)

        view = img_np[:, src_cols]   # (H, N [, C])

        if flip_spatial_y:
            view = view[::-1]

        # https://textbooks.cs.ksu.edu/cis580/10-tile-maps/03-2d-and-1d-arrays/index.html
        # converting an index into 2d coordinates, would be:
        #   tile_col = v // cols
        #   tile_row = v  % cols   (0 = bottom)
        tile_col = v % cols
        tile_row = v  // cols
        x0 = tile_col * N
        # row 0 is the bottom strip → invert to pixel coords
        y0 = (rows - 1 - tile_row) * H
        quilt_np[y0: y0 + H, x0: x0 + N] = view
    cv2.imwrite("quilt_v5.png", quilt_np)
    return quilt_np


if __name__ == "__main__":
    integral_to_quilt(
        image_path      = "Test.png",
        num_hogels      = 819,
        directional_res = 81,
        display_fov_deg = 60.0,
        z_cam_hogels    = None,
        flip_spatial_y  = False,
    )