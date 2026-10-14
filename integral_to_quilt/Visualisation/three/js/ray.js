/**
 * ray.js
 * ------
 * One responsibility: turn an (azimuth, elevation) pair into a
 * correctly oriented cylinder whose base sits at the local origin.
 *
 * This is the geometric heart of the recreation, so the orientation
 * is done explicitly rather than by eyeballed Euler angles.
 */

import * as THREE from 'three';

const UP = new THREE.Vector3(0, 1, 0);

/**
 * Unit direction vector for a spherical (azimuth, elevation) pair.
 * Exported because emitter.js reuses it to place markers along a ray.
 */
export function directionFromAngles(azimuthDeg, elevationDeg) {
  const az = THREE.MathUtils.degToRad(azimuthDeg);
  const el = THREE.MathUtils.degToRad(elevationDeg);
  const cosEl = Math.cos(el);
  return new THREE.Vector3(
    cosEl * Math.cos(az),
    Math.sin(el),
    cosEl * Math.sin(az)
  ).normalize();
}

/**
 * Build a single ray mesh.
 *
 * CylinderGeometry is +Y-aligned and centred on the origin. We shift
 * it up by length/2 so the base lands at (0,0,0), then rotate the
 * whole mesh so +Y maps onto the requested direction. The base stays
 * pinned at the origin; only the tip swings.
 */
export function createRay({
  azimuth,
  elevation,
  length = 3.4,
  radius = 0.11,
  color = 0xffffff,
  opacity = 0.6,
  emissiveIntensity = 0.15,
  radialSegments = 32,
}) {
  const dir = directionFromAngles(azimuth, elevation);

  const geometry = new THREE.CylinderGeometry(
    radius,
    radius,
    length,
    radialSegments,
    1,
    false
  );
  geometry.translate(0, length / 2, 0); // base at local origin

  const material = new THREE.MeshStandardMaterial({
    color,
    transparent: opacity < 1,
    opacity,
    roughness: 0.35,
    metalness: 0.0,
    emissive: new THREE.Color(color),
    emissiveIntensity,
  });

  const mesh = new THREE.Mesh(geometry, material);
  mesh.quaternion.setFromUnitVectors(UP, dir);
  mesh.castShadow = true;

  // Stash for any consumer that wants to follow the ray later.
  mesh.userData.direction = dir;
  mesh.userData.length = length;

  return mesh;
}
