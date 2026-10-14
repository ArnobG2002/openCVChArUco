/**
 * main.js
 * -------
 * Entry point and orchestration only. It owns no geometry knowledge:
 * it reads CONFIG, asks the factories to build emitters, sets up the
 * render pipeline, and drives the frame loop.
 */

import { createApp } from './sceneSetup.js';
import { createComposer } from './postprocessing.js';
import { createEmitter } from './emitter.js';
import { CONFIG } from './config.js';

const container = document.getElementById('app');

const { renderer, scene, camera, controls, onResize } = createApp({
  container,
  config: CONFIG,
});

// Content: build every emitter described in the config.
for (const emitterSpec of CONFIG.emitters) {
  scene.add(createEmitter(emitterSpec));
}

// Render pipeline (bloom).
const { composer } = createComposer(renderer, scene, camera, CONFIG.bloom);
onResize((w, h) => composer.setSize(w, h));

// Frame loop.
function animate() {
  requestAnimationFrame(animate);
  controls.update();
  composer.render();
}
animate();
