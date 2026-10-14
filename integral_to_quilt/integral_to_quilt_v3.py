"""
integral_to_quilt_v3.py
========================
Perspective-correct integral image → quilt conversion.

Config source (from JSON):
    spatialResolution:    [819, 455]   → num_hogels=819, spatial_res_y=455
    directionalResolution:[81, 1]      → directional_res=81 (HPO)
    displayFOV:           [60, 1]      → maxAngle = tan(30°) = 0.57735

Why v2 was wrong
-----------------
v2 used the "assembled view": for every hogel h in tile v, it sampled
directional index dx = v (same direction for all hogels). This produces
an orthographic view — near and far edges of the table appear at the
same width — because all hogels look in the same parallel direction.

The correct algorithm (matching C++ getLightFieldStruct)
---------------------------------------------------------
Place a virtual camera for each view v at:

    x_cam_v = display_center + z_cam * tan(θ_v)

where tan(θ_v) = (1 - 2*v/(D-1)) * maxAngle  (C++ directional convention).

A ray from this camera hits hogel h at angle:

    tan(θ_ray) = (x_cam_v - h) / z_cam          # ray direction at hogel h

Mapping to the C++ directional index formula:

    angles.x  = -(dir.x/dir.z) / maxAngle
              = -(x_cam_v - h) / (z_cam * maxAngle)  [note negation]
    angles.x  = angles.x/2 + 0.5
    dx        = (D-1) * angles.x

Substituting and simplifying gives the closed-form per-hogel directional index:

    dx(h, v)  = v + (D-1) * (h - display_center) / (2 * z_cam * maxAngle)

Choosing z_cam
--------------
z_cam is the distance (in hogel-pitch units) of the virtual camera plane
from the display. It controls how much perspective appears in each tile.

Natural viewing distance (used as default):
    z_cam = num_hogels / (2 * maxAngle)

This sets the camera FOV to exactly match the light field directional FOV,
so the full display width fills each tile and parallax spans the full
directional range. With this z_cam the formula simplifies to:

    dx(h, v) = v + (D-1) * (h - display_center) / num_hogels

For a smaller z_cam (camera closer to display) the perspective is stronger.
For a larger z_cam (camera further away) the perspective weakens toward
the assembled orthographic view.

Physical parameters (from config JSON)
---------------------------------------
    capturePlaneDimensions : [13.656, 7.632]
    hogel_pitch_mm         : 13.656 / 819 ≈ 0.01667 units
    natural z_cam (units)  : 13.656 / (2 * tan30°) ≈ 11.82 units
    natural z_cam (hogels) : 819 / (2 * 0.57735) ≈ 709 hogels
"""

import numpy as np
from PIL import Image
import argparse
import json
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
) -> Image.Image:
    """
    Parameters
    ----------
    image_path      : path to HPO integral image
                      Width must equal num_hogels * directional_res
    num_hogels      : number of hogels (spatial positions) horizontally
    directional_res : number of directional views per hogel  (= D)
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
    img    = Image.open(image_path)
    img_np = np.array(img)
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
        z_cam_hogels = N / (1.0 * max_angle)

    display_center = (N - 1) / 2.0          # hogel-index of display centre

    # -----------------------------------------------------------------------
    # Perspective-correct view synthesis
    #
    # For view v and hogel h, the required directional index is:
    #   dx(h,v) = v + (D-1) * (h - display_center) / (2 * z_cam * maxAngle)
    #
    # With the natural z_cam this simplifies to:
    #   dx(h,v) = v + (D-1) * (h - display_center) / N
    # -----------------------------------------------------------------------
    h_indices = np.arange(N, dtype=np.float64)

    # Pre-compute the per-hogel parallax offset (independent of v)
    parallax = (D - 1) * (h_indices - display_center) / (2.0 * z_cam_hogels * max_angle)
    print(parallax)
    quilt_np = np.empty_like(img_np)

    for v in range(D):
        dx_float = v + parallax                                   # (N,)
        dx_int   = np.clip(np.round(dx_float).astype(np.int32),
                           0, D - 1)                             # (N,)

        # Integral image column for hogel h at direction dx_int[h]:
        #   col = h * D + dx_int[h]
        src_cols = (np.arange(N, dtype=np.int32) * D) + dx_int  # (N,)

        view = img_np[:, src_cols]   # (H, N [, C])

        if flip_spatial_y:
            view = view[::-1]

        # was:  dst_start = v * N
        dst_start = (D - 1 - v) * N   # reversed to match C++ assembly convention
        quilt_np[:, dst_start: dst_start + N] = view

    return Image.fromarray(quilt_np)


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
        "--output", type=str, default="quilt_v3.png",
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
    quilt.save(args.output)
    print(
        f"Saved quilt → {args.output}\n"
        f"  {D} tiles × {N} px wide, height {quilt.height} px\n"
        f"  Total quilt size: {quilt.width} × {quilt.height}"
    )


if __name__ == "__main__":
    main()
