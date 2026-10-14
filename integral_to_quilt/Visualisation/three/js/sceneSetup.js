/**
 * sceneSetup.js
 * -------------
 * Infrastructure: everything that is "the viewer" rather than "the
 * content". Renderer, scene, camera, lights, orbit controls, and the
 * resize handler. Returns the handles main.js needs to drive a frame.
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

function addLights(scene) {
  // Soft studio fill — gives the grey, even ambience of the reference.
  scene.add(new THREE.HemisphereLight(0xffffff, 0x404040, 0.7));
  scene.add(new THREE.AmbientLight(0xffffff, 0.25));

  // Key light, also the shadow caster that streaks the plate.
  const key = new THREE.DirectionalLight(0xffffff, 1.1);
  key.position.set(6, 10, 6);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  key.shadow.camera.near = 1;
  key.shadow.camera.far = 40;
  key.shadow.camera.left = -10;
  key.shadow.camera.right = 10;
  key.shadow.camera.top = 10;
  key.shadow.camera.bottom = -10;
  key.shadow.bias = -0.0005;
  scene.add(key);

  return key;
}

export function createApp({ container, config }) {
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(config.background);

  const { fov, position, target } = config.camera;
  const camera = new THREE.PerspectiveCamera(
    fov,
    window.innerWidth / window.innerHeight,
    0.1,
    100
  );
  camera.position.set(position.x, position.y, position.z);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(target.x, target.y, target.z);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.minDistance = 4;
  controls.maxDistance = 25;
  controls.update();

  addLights(scene);

  // Resize is owned here; main.js subscribes for anything extra
  // (e.g. the composer) via the returned callback list.
  const onResizeCallbacks = [];
  function onResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    for (const cb of onResizeCallbacks) cb(window.innerWidth, window.innerHeight);
  }
  window.addEventListener('resize', onResize);

  return {
    renderer,
    scene,
    camera,
    controls,
    onResize: (cb) => onResizeCallbacks.push(cb),
  };
}
