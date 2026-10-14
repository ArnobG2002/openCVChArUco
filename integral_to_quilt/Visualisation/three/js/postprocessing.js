/**
 * postprocessing.js
 * -----------------
 * The bloom pipeline, isolated so the render path is swappable. If you
 * ever want the raw look, main.js can call renderer.render() instead
 * and this module simply goes unused.
 *
 * OutputPass performs tone mapping (reading renderer.toneMapping) and
 * the linear->sRGB conversion at the very end, so it must come last.
 */

import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

export function createComposer(renderer, scene, camera, bloom = {}) {
  const composer = new EffectComposer(renderer);

  composer.addPass(new RenderPass(scene, camera));

  const bloomPass = new UnrealBloomPass(
    new THREE.Vector2(window.innerWidth, window.innerHeight),
    bloom.strength ?? 0.5,
    bloom.radius ?? 0.4,
    bloom.threshold ?? 0.82
  );
  composer.addPass(bloomPass);

  composer.addPass(new OutputPass());

  return { composer, bloomPass };
}
