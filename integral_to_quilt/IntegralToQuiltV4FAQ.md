## 12. The Key Observation
> the near edge of the table top is a narrower horizontal line than the far edge.
> Good around the left/right tiles, bad around the middle tiles.

This is a very important pair of clues. Let me reason carefully.

**"Good around left/right tiles, bad around the middle tiles"**

The middle tiles correspond to direction `dx ≈ D/2` — all hogels looking straight ahead
(θ ≈ 0). The left/right tiles correspond to extreme angles (θ ≈ ±θ_max).

The assembled view at the center direction (all hogels looking straight ahead
simultaneously) is essentially an **orthographic projection** — every hogel contributes
the pixel directly in front of it. 

[Willats](https://books.google.ca/books?id=UAKljsHF2DkC&lpg=PR11&ots=ZzLdl6EdNN&dq=in%20orthographic%20projection%2C%20near%20and%20far%20edges%20of%20the%20table%20appear%20at%20their%20physical%20width&lr&pg=PA10#v=onepage&q&f=false) defines orthogonal projection as the system in which the projection rays are parallel and intersect the picture plane at right angles: rather like taking a photograph of an object with a powerful telephoto lens from a considerable distance.

In orthographic projection, near and far edges of the
table appear at their **physical width**, which for a rectangular table means near = far.
No foreshortening. So near doesn't appear wider than far — and the user perceives this as
near appearing "shorter."

At extreme angles, the 3D shape of the table itself creates perspective-like cues — you
see the side panels, legs become prominent, the near face becomes larger naturally from the
scene geometry. So those tiles accidentally look more correct.

**The fundamental issue is this:**

Having generated a light field image, we needed to develop a method to view the generated images [necec2021](https://www.cs.mun.ca/~mhamilton/papers/nwells-hamilton-Necec2021.pdf). This began with generating 2D images from the light field based on orthographic projections of the light field (taking a single pixel from each hogel all corresponding the same light ray angle) [necec2021](https://www.cs.mun.ca/~mhamilton/papers/nwells-hamilton-Necec2021.pdf). Once this process was complete an output image would be saved and could be viewed [necec2021](https://www.cs.mun.ca/~mhamilton/papers/nwells-hamilton-Necec2021.pdf).
The Python code does a **light field assembly** — one pixel per hogel at a fixed
direction. This produces an orthographic view at center direction. 

The C++ does proper
**perspective view synthesis** — it casts a ray from a virtual camera, finds where it hits [unity](https://docs.unity3d.com/6000.4/Documentation/Manual/CameraRays.html)
the display surface, computes the hogel and directional index from that intersection, and
samples accordingly. That produces a true perspective view where near appears wider.

These are two fundamentally different operations. The Python code isn't doing what the C++
does. To match the C++, the Python would need to implement the same ray-based view
synthesis:

```
for each pixel (px, py) in the output view:
    compute ray direction from virtual camera through (px, py)
    find intersection with display plane → hogel position
    compute directional index from ray angle at that hogel
    sample integral image at (hogel * directional_res + directional_index, py)
```

This requires knowing the camera distance, display geometry, and FOV — parameters not in
the original script at all. That's why it can't be fixed with a simple line change.

---

## 13. What to Feed the Display?

> In orthographic projection, near and far edges of the table appear at their physical
> width, which for a rectangular table means near = far. No foreshortening. So near
> doesn't appear wider than far — and the user perceives this as near appearing "shorter."
>
> Okay. So at the end of the day, the display expects a quilt. What am I going to feed it?


The practical answer depends on what's consuming the quilt.


Light field displays fundamentally face substantial computational overhead in rendering due to their unique optical design. Unlike conventional single-view 2D displays, they require the generation of multiple perspective views to reconstruct the full light field, necessitating a dense array of rays projected at precise angles [nvidia](https://arxiv.org/html/2508.18540v1).

**If the C++ OptiX renderer is in the pipeline** — don't convert at all. The C++ already
reads the integral image and synthesizes correct perspective views via `getLightFieldStruct`.
The quilt conversion is redundant; the display should consume the integral image through
the C++ path.

**If the display requires a pre-computed quilt file** — the Python assembled-view quilt is
the *wrong* input. Each tile in a proper quilt is a perspective view from a single camera
position.

The assembled view is not that — it's all hogels looking in the same direction
simultaneously, which is an orthographic sampling. On the display, this produces a
flattened or incorrectly foreshortened 3D image.

**To generate a correct quilt from the integral image in Python**, you need to implement
view synthesis — the same logic as `getLightFieldStruct`:

```
for each view v (camera position x_cam_v):
    for each output pixel (px, py):
        ray_angle = camera_fov * (px / view_width - 0.5)
        x_display = x_cam_v + z_cam * tan(ray_angle)
        hogel = floor(x_display / hogel_pitch)
        dir_angle = ray_angle
        dx = round((D-1) * (0.5 - dir_angle / fov_total))
        quilt_pixel[v][px, py] = integral_image[py, hogel * D + dx]
```

This requires: hogel pitch, display width, camera distance `z_cam`, camera FOV, and
number of views — parameters that `integral_to_quilt_v2.py` currently has no knowledge of.

**Short answer**: if you need to feed a quilt to the display and the C++ path isn't
available, `integral_to_quilt_v2.py` is the best you can do with the current information,
but expect flat/compressed depth. For a geometrically correct quilt, you need the
display's physical parameters and a view synthesis loop like the one above.

---

