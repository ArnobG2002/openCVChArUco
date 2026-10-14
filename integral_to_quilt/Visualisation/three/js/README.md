# Light Field Ray Fan — Three.js

A recreation of two emitter plates: a left fan of coloured directional
rays (with a bead riding the green ray) and a right red fan with a soft
ground glow. Orbitable.

## Run it

ES modules can't be loaded over `file://`, so serve the folder over
HTTP. Any static server works:

```bash
# Python (no install)
python3 -m http.server 8000

# or Node
npx serve .
```

Then open <http://localhost:8000/>.

## Layout

```
index.html            markup + import map (pins the three.js version)
css/styles.css        presentation only
js/
  config.js           the scene AS DATA — edit angles/colours here
  ray.js              (azimuth, elevation) -> oriented cylinder + the direction math
  plate.js            translucent slab factory
  glow.js             additive radial-gradient ground glow
  emitter.js          composes plate + rays + glow + markers into one group
  sceneSetup.js       renderer, camera, lights, controls, resize
  postprocessing.js   EffectComposer + UnrealBloom pipeline
  main.js             entry point: config -> factories -> render loop
```

The dependency direction is one-way: `main` → factories → `ray`/`plate`/
`glow`. `config.js` imports nothing, so it stays pure description.

## Tweaking

Everything visible is driven from `js/config.js`. To reshape a fan,
change each ray's `azimuth` / `elevation` (degrees). Convention:

- `azimuth` — around the vertical axis in the ground plane; 0° → +X,
  increasing toward +Z.
- `elevation` — up from the ground plane; 90° is straight up.

Each ray's base is pinned to its emitter's convergence point; only the
tip swings as you change the angles.
