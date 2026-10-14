/**
 * emitter.js
 * ----------
 * Composition layer. Takes one emitter spec from config and assembles
 * a self-contained THREE.Group: a plate, its fan of rays, an optional
 * ground glow, and any per-ray markers (the blue bead on the green
 * ray). Everything is parented to a group placed at the emitter's
 * position, so the whole assembly moves as a unit.
 */

import * as THREE from 'three';
import { createPlate } from './plate.js';
import { createRay, directionFromAngles } from './ray.js';
import { createGlow } from './glow.js';

function createMarker(raySpec) {
  const dir = directionFromAngles(raySpec.azimuth, raySpec.elevation);
  const t = raySpec.marker.t ?? 0.5;
  const length = raySpec.length ?? 3.4;
  const pos = dir.clone().multiplyScalar(t * length);

  const color = raySpec.marker.color ?? 0x3a6dd6;
  const mesh = new THREE.Mesh(
    new THREE.SphereGeometry(raySpec.marker.radius ?? 0.18, 32, 16),
    new THREE.MeshStandardMaterial({
      color,
      emissive: new THREE.Color(color),
      emissiveIntensity: 0.4,
      roughness: 0.3,
      metalness: 0.0,
    })
  );
  mesh.position.copy(pos);
  mesh.castShadow = true;
  return mesh;
}

export function createEmitter(spec) {
  const group = new THREE.Group();

  group.add(createPlate(spec.plate));

  if (spec.glow) {
    group.add(createGlow(spec.glow));
  }

  for (const raySpec of spec.rays) {
    group.add(createRay(raySpec));
    if (raySpec.marker) {
      group.add(createMarker(raySpec));
    }
  }

  if (spec.position) {
    group.position.set(
      spec.position.x ?? 0,
      spec.position.y ?? 0,
      spec.position.z ?? 0
    );
  }

  return group;
}
