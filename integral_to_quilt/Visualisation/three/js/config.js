/**
 * config.js
 * ---------
 * The scene as data. Nothing here imports three.js — it is pure
 * description, consumed by the factories in emitter.js / ray.js.
 *
 * Angle convention (see ray.js for the math):
 *   azimuth   — degrees around the vertical (+Y) axis, in the XZ plane.
 *               0° points toward +X, increasing toward +Z.
 *   elevation — degrees up from the ground (XZ) plane.
 *               90° is straight up (+Y).
 *
 * Each ray's BASE sits at its emitter's origin (the convergence point
 * on the plate's top surface); the ray extends outward along its
 * (azimuth, elevation) direction for `length` units.
 */

export const CONFIG = {
  background: 0x3d3d3d,

  // Post-processing bloom. Higher threshold => only the brightest
  // (emissive) pixels bloom, keeping the plate matte.
  bloom: { strength: 0.55, radius: 0.5, threshold: 0.8 },

  camera: {
    fov: 35,
    position: { x: 0, y: 4.5, z: 10 },
    target: { x: 0, y: 0.8, z: 0 },
  },

  emitters: [
    // ---- Left: the multi-colour directional fan ------------------
    {
      position: { x: -3.2, y: 0, z: 0 },
      plate: { size: 4, thickness: 0.2 },
      rays: [
        { azimuth: 205, elevation: 55, length: 3.2, color: 0xb8a878, opacity: 0.34, emissiveIntensity: 0.04 }, // faded tan
        { azimuth: 155, elevation: 62, length: 3.6, color: 0xe3c64a, opacity: 0.6 },                            // yellow
        { azimuth: 110, elevation: 82, length: 3.4, color: 0x3a6dd6, opacity: 0.62 },                           // blue (near-vertical)
        {
          azimuth: 60, elevation: 58, length: 3.9, color: 0x41ad57, opacity: 0.62,                              // green, carries the bead
          marker: { t: 0.6, radius: 0.18, color: 0x3a6dd6 },
        },
      ],
    },

    // ---- Right: the red fan with a ground glow -------------------
    {
      position: { x: 3.2, y: 0, z: 0 },
      plate: { size: 4, thickness: 0.2 },
      glow: { radius: 1.7, color: '230,60,60' },
      rays: [
        { azimuth: 35, elevation: 60, length: 3.3, color: 0xd83b3b, opacity: 0.6 },
        { azimuth: 70, elevation: 74, length: 3.4, color: 0xd83b3b, opacity: 0.6 },
        { azimuth: 100, elevation: 66, length: 3.3, color: 0xd83b3b, opacity: 0.6 },
        { azimuth: 130, elevation: 72, length: 3.4, color: 0xd83b3b, opacity: 0.6 },
        { azimuth: 95, elevation: 54, length: 3.2, color: 0xd83b3b, opacity: 0.55 },
      ],
    },
  ],
};
