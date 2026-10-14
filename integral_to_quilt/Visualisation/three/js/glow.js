/**
 * glow.js
 * -------
 * The soft pool of light under the red fan. A radial-gradient texture
 * painted to an offscreen canvas, mapped onto a flat plane with
 * additive blending so it brightens whatever is beneath it. Bloom in
 * the post pass does the rest of the bleed.
 */

import * as THREE from 'three';

function radialTexture(rgb) {
  const s = 256;
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = s;

  const ctx = canvas.getContext('2d');
  const g = ctx.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
  g.addColorStop(0.0, `rgba(${rgb},0.95)`);
  g.addColorStop(0.35, `rgba(${rgb},0.5)`);
  g.addColorStop(1.0, `rgba(${rgb},0.0)`);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, s, s);

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

export function createGlow({ radius = 1.7, color = '230,60,60' } = {}) {
  const geometry = new THREE.PlaneGeometry(radius * 2, radius * 2);

  const material = new THREE.MeshBasicMaterial({
    map: radialTexture(color),
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false, // never occlude; only ever adds light
  });

  const mesh = new THREE.Mesh(geometry, material);
  mesh.rotation.x = -Math.PI / 2; // lay flat on the plate
  mesh.position.y = 0.012; // float just above the top face to avoid z-fighting

  return mesh;
}
