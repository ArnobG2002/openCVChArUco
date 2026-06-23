import numpy as np
import argparse
import json
import cv2
import os


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
        z_cam_hogels = -N / (1.0 * max_angle)

    display_center = (N - 1) / 2.0          # hogel-index of display centre

    # -----------------------------------------------------------------------
    # Perspective-correct view synthesis
    # -----------------------------------------------------------------------
    h_indices = np.arange(N, dtype=np.float64)

    # Pre-compute the per-hogel parallax offset (independent of v)
    parallax = (D - 1) * (1+( display_center - h_indices) / (2.0 * z_cam_hogels * max_angle))
    
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
        dx_float = -v + parallax                                   # (N,)
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

    return quilt_np


# ---------------------------------------------------------------------------
# Config-file helper
# ---------------------------------------------------------------------------

def load_config(config_path: str) -> dict:
    """
    Parse the JSON config and return keyword arguments for integral_to_quilt().
    Handles the structure from the vaclab config format.
    """
    with open(config_path) as f:
        cfg = json.load(f)

    lf = cfg.get("lightFieldAttributes", {})
    kwargs = {}

    if "spatialResolution" in lf:
        kwargs["num_hogels"] = int(lf["spatialResolution"][0])

    if "directionalResolution" in lf:
        kwargs["directional_res"] = int(lf["directionalResolution"][0])

    if "displayFOV" in lf:
        kwargs["display_fov_deg"] = float(lf["displayFOV"][0])

    return kwargs


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Integral image → perspective-correct quilt  "
            "(matches C++ getLightFieldStruct convention)"
        )
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help=(
            "Path to the JSON config file (e.g. the vaclab config). "
            "Overrides --num_hogels, --directional_res, --display_fov_deg "
            "when provided."
        )
    )
    parser.add_argument(
        "--image_path", type=str,
        default="Test.png",
        help="Path to the HPO integral image"
    )
    parser.add_argument(
        "--num_hogels", type=int,
        default=_DEFAULTS["num_hogels"],
        help="Number of hogels (spatial positions) horizontally"
    )
    parser.add_argument(
        "--directional_res", type=int,
        default=_DEFAULTS["directional_res"],
        help="Directional resolution (views per hogel)"
    )
    parser.add_argument(
        "--display_fov_deg", type=float,
        default=_DEFAULTS["display_fov_deg"],
        help="Horizontal full-FOV of the light field in degrees"
    )
    parser.add_argument(
        "--z_cam_hogels", type=float, default=None,
        help=(
            "Virtual camera distance from display in hogel-pitch units. "
            "Default: num_hogels / (2*tan(fov/2))  [natural viewing distance]"
        )
    )
    parser.add_argument(
        "--flip_spatial_y", action="store_true",
        help="Flip each tile vertically (use if output appears upside-down)"
    )
    parser.add_argument(
        "--output", type=str, default="quilt_v4.png",
        help="Output quilt image path"
    )

    args = parser.parse_args()

    # Keyword args from CLI
    kwargs = dict(
        num_hogels      = args.num_hogels,
        directional_res = args.directional_res,
        display_fov_deg = args.display_fov_deg,
        z_cam_hogels    = args.z_cam_hogels,
        flip_spatial_y  = args.flip_spatial_y,
    )

    # Config file overrides (if provided)
    if args.config:
        cfg_kwargs = load_config(args.config)
        kwargs.update(cfg_kwargs)
        print(f"Loaded config from {args.config}: {cfg_kwargs}")

    # Derived display info
    N = kwargs["num_hogels"]
    D = kwargs["directional_res"]
    fov = kwargs["display_fov_deg"]
    max_angle = np.tan(np.radians(fov / 2.0))
    z_cam = kwargs["z_cam_hogels"] if kwargs["z_cam_hogels"] else N / (2.0 * max_angle)

    print(
        f"\nParameters:\n"
        f"  hogels          : {N}\n"
        f"  directional_res : {D}\n"
        f"  display FOV     : {fov}°  → maxAngle = {max_angle:.5f}\n"
        f"  z_cam           : {z_cam:.1f} hogels "
        f"({'natural' if kwargs['z_cam_hogels'] is None else 'custom'})\n"
        f"  parallax coeff  : {(D-1)/(2*z_cam*max_angle):.4f} dx-steps per hogel\n"
        f"  flip_spatial_y  : {kwargs['flip_spatial_y']}\n"
    )

    quilt = integral_to_quilt(args.image_path, **kwargs)
    cv2.imwrite(args.output, quilt)
    cols = int(np.floor(np.sqrt(D)))
    while D % cols != 0:
        cols -= 1
    rows = D // cols
    print(
        f"Saved quilt → {args.output}\n"
        f"  Grid: {cols} cols × {rows} rows  (tile 0 = bottom-left, tile {D-1} = top-right)\n"
        f"  Tile size: {N} × {quilt.shape[0] // rows} px\n"
        f"  Total quilt size: {quilt.shape[1]} × {quilt.shape[0]}"
    )


if __name__ == "__main__":
    main()