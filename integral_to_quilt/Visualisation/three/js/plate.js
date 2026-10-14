/**
 * plate.js
 * --------
 * The frosted slab the rays emerge from. Positioned so its TOP
 * surface lies at y = 0, which is the convergence plane the rays
 * are anchored to.
 */

import * as THREE from 'three';

export function createPlate({
  size = 4,
  thickness = 0.2,
  color = 0xffffff,
  opacity = 0.42,
} = {}) {
  const geometry = new THREE.BoxGeometry(size, thickness, size);

  const material = new THREE.MeshStandardMaterial({
    color,
    transparent: true,
    opacity,
    roughness: 0.6,
    metalness: 0.0,
  });

  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.y = -thickness / 2; // push body down so the top is at y = 0
  mesh.receiveShadow = true;

  return mesh;
}
