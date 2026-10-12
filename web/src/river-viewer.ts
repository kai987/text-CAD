import { Box3, Color, DirectionalLight, HemisphereLight, Mesh, Object3D, OrthographicCamera, PCFShadowMap, Raycaster, Scene, Vector2, Vector3, WebGLRenderer } from 'three';
import type { Material, MeshStandardMaterial } from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { asset, assetSha256 } from './data';
import { startModelLoad } from './model-resource';
import type { ModelProgress } from './model-resource';
import { createDemandRenderScheduler } from './demand-render';
import { riverGroups } from './river-copy';
import type { RiverGroupId } from './river-copy';
import { themePalette } from './theme-preferences';
import type { ResolvedTheme } from './theme-preferences';
import { bindCadNodes } from './model-scene';

export interface RiverViewer {
  visibility: (values: Record<RiverGroupId, boolean>) => void;
  camera: (mode: 'iso' | 'top') => void;
  theme: (theme: ResolvedTheme) => void;
  label: (label: string) => void;
  dispose: () => void;
}
function disposeModel(root: Object3D) {
  const materials = new Set<Material>();
  root.traverse(node => {
    if (!(node instanceof Mesh)) return;
    node.geometry.dispose();
    (Array.isArray(node.material) ? node.material : [node.material]).forEach(material => materials.add(material));
  });
  materials.forEach(material => material.dispose());
}

export function createRiverViewer(host: HTMLElement, options: {
  theme: ResolvedTheme; label: string; onReady: () => void; onError: () => void;
  onProgress: (progress: ModelProgress) => void; onSelection: (group: RiverGroupId | null) => void;
}): RiverViewer {
  const renderer = new WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = PCFShadowMap;
  // The planting and sunlight are static. Camera orbit does not rerender a
  // shadow map; visibility changes explicitly invalidate the cached shadows.
  renderer.shadowMap.autoUpdate = false;
  renderer.setClearColor(themePalette[options.theme].canvasBackground);
  const canvas = renderer.domElement;
  canvas.tabIndex = 0;
  canvas.setAttribute('role', 'img');
  canvas.setAttribute('aria-label', options.label);
  canvas.dataset.renderStrategy = 'demand';
  canvas.dataset.renderedFrames = '0';
  host.prepend(canvas);
  const scene = new Scene();
  const sky = new HemisphereLight(0xffffff, 0x739263, 2.2);
  const sun = new DirectionalLight(0xfff3df, 2.6);
  sun.position.set(-80, 150, 80);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -130, right: 130, top: 130, bottom: -130, near: .1, far: 420 });
  sun.shadow.bias = -.00015;
  sun.shadow.normalBias = .08;
  scene.add(sky, sun);
  const camera = new OrthographicCamera(-100, 100, 100, -100, 0.1, 2000);
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = 0.13;
  controls.zoomToCursor = true;
  controls.minZoom = 0.2;
  controls.maxZoom = 24;
  controls.maxPolarAngle = Math.PI * 0.91;
  controls.listenToKeyEvents(canvas);
  let disposed = false, inViewport = true, contextLost = false, frames = 0, shadowUpdates = 0;
  let root: Object3D | null = null;
  let view: 'iso' | 'top' = 'iso';
  let halfHeight = 80;
  let fitHorizontal = 80, fitVertical = 80;
  const bound = new Box3();
  const groupNodes = new Map<RiverGroupId, Object3D[]>();
  const nodeGroups = new Map<Object3D, RiverGroupId>();
  let visibility: Record<RiverGroupId, boolean> = Object.fromEntries(Object.keys(riverGroups).map(id => [id, true])) as Record<RiverGroupId, boolean>;
  const scheduler = createDemandRenderScheduler({
    draw() {
      availability();
      if (disposed || canvas.dataset.renderVisibility !== 'visible') return;
      controls.update();
      const updateShadow = renderer.shadowMap.needsUpdate;
      renderer.render(scene, camera);
      if (updateShadow) canvas.dataset.shadowUpdates = String(++shadowUpdates);
      canvas.dataset.renderedFrames = String(++frames);
      canvas.dataset.cameraPose = JSON.stringify({ position: camera.position.toArray(), target: controls.target.toArray(),
        up: camera.up.toArray(), zoom: camera.zoom, frustum: [camera.left, camera.right, camera.top, camera.bottom] });
    },
    requestFrame: callback => requestAnimationFrame(callback), cancelFrame: id => cancelAnimationFrame(id),
    onState: state => { canvas.dataset.renderState = state; },
  });
  function availability() {
    const state = document.hidden ? 'document-hidden' : contextLost ? 'context-lost'
      : !host.clientWidth || !host.clientHeight ? 'layout-hidden' : !inViewport ? 'offscreen' : 'visible';
    canvas.dataset.renderVisibility = state;
    scheduler.setActive(!disposed && state === 'visible');
  }
  function resize() {
    availability();
    const width = host.clientWidth, height = host.clientHeight;
    if (!width || !height || disposed) return;
    renderer.setSize(width, height, false);
    const aspect = width / height;
    halfHeight = Math.max(fitVertical, fitHorizontal / aspect) * 1.13;
    camera.left = -halfHeight * aspect; camera.right = halfHeight * aspect;
    camera.top = halfHeight; camera.bottom = -halfHeight;
    camera.updateProjectionMatrix(); scheduler.invalidate();
  }
  function fit(mode: 'iso' | 'top') {
    view = mode;
    if (!root || !host.clientWidth || !host.clientHeight) return;
    const center = bound.getCenter(new Vector3());
    controls.target.copy(center);
    camera.up.set(0, mode === 'top' ? 0 : 1, mode === 'top' ? -1 : 0);
    camera.position.copy(center).add(mode === 'top' ? new Vector3(0, 300, 0) : new Vector3(180, 180, 220));
    camera.lookAt(center);
    camera.updateMatrixWorld();
    // Fit all eight bounding-box corners to the actual viewport rather than assuming a house-sized model.
    let horizontal = 0, vertical = 0;
    for (const x of [bound.min.x, bound.max.x]) for (const y of [bound.min.y, bound.max.y]) for (const z of [bound.min.z, bound.max.z]) {
      const point = new Vector3(x, y, z).applyMatrix4(camera.matrixWorldInverse);
      horizontal = Math.max(horizontal, Math.abs(point.x));
      vertical = Math.max(vertical, Math.abs(point.y));
    }
    fitHorizontal = horizontal; fitVertical = vertical;
    camera.zoom = 1;
    controls.update(); resize();
  }
  function applyVisibility(values: Record<RiverGroupId, boolean>) {
    visibility = { ...values };
    for (const [id, nodes] of groupNodes) nodes.forEach(node => { node.visible = values[id]; });
    canvas.dataset.visibleGroups = JSON.stringify(Object.keys(riverGroups).filter(id => values[id as RiverGroupId]));
    renderer.shadowMap.needsUpdate = true;
    scheduler.invalidate();
  }
  const changed = () => { scheduler.invalidate(); };
  controls.addEventListener('change', changed);
  const observer = new ResizeObserver(() => {
    // Keep the current orbit and zoom on ordinary resizes and translated text changes.
    if (!frames && root) fit(view); else resize();
  });
  observer.observe(host);
  const intersection = typeof IntersectionObserver === 'undefined' ? null : new IntersectionObserver(entries => {
    inViewport = entries.at(-1)?.isIntersecting ?? true;
    availability();
  });
  intersection?.observe(host);
  const documentVisibility = () => availability();
  document.addEventListener('visibilitychange', documentVisibility);
  const lost = (event: Event) => { event.preventDefault(); contextLost = true; availability(); options.onError(); };
  canvas.addEventListener('webglcontextlost', lost);
  let pointerDown: { x: number; y: number } | null = null;
  const down = (event: PointerEvent) => { pointerDown = { x: event.clientX, y: event.clientY }; };
  const up = (event: PointerEvent) => {
    if (!root || !pointerDown || Math.hypot(event.clientX - pointerDown.x, event.clientY - pointerDown.y) > 5) { pointerDown = null; return; }
    pointerDown = null;
    const rect = canvas.getBoundingClientRect();
    const point = new Vector2((event.clientX - rect.left) / rect.width * 2 - 1, -(event.clientY - rect.top) / rect.height * 2 + 1);
    const ray = new Raycaster(); ray.setFromCamera(point, camera);
    for (const hit of ray.intersectObject(root, true)) {
      let node: Object3D | null = hit.object;
      let group: RiverGroupId | undefined;
      let visible = true;
      while (node) { if (!node.visible) visible = false; group ??= nodeGroups.get(node); node = node.parent; }
      if (group && visible) { options.onSelection(group); return; }
    }
    options.onSelection(null);
  };
  canvas.addEventListener('pointerdown', down); canvas.addEventListener('pointerup', up);
  availability(); resize();
  const loader = new GLTFLoader();
  const load = startModelLoad({
    url: asset('GLB/river_demo.glb'), compressed: !!assetSha256('GLB/river_demo.glb.gz'), compressedUrl: asset('GLB/river_demo.glb.gz'),
    expectedSha256: assetSha256('GLB/river_demo.glb'),
    parse: bytes => loader.parseAsync(bytes, ''),
    onProgress: options.onProgress,
    onError: error => { console.error('River model load failed.', error); options.onError(); },
    disposeLate: gltf => disposeModel(gltf.scene),
    onLoad(gltf) {
      try {
        const cadNodes = bindCadNodes(gltf);
        for (const [id, names] of Object.entries(riverGroups)) {
          const nodes = names.map(name => cadNodes.get(name));
          if (nodes.some(node => !node)) throw new Error(`Missing river component in release: ${id}`);
          groupNodes.set(id as RiverGroupId, nodes as Object3D[]);
          (nodes as Object3D[]).forEach(node => nodeGroups.set(node, id as RiverGroupId));
        }
        const water = groupNodes.get('water')!;
        let treeCrowns = 0;
        gltf.scene.traverse(child => {
          if (!(child instanceof Mesh)) return;
          const name = String(child.userData.cadName);
          child.castShadow = name.startsWith('Landscape:trees:');
          child.receiveShadow = !name.startsWith('River:water');
          if (name.startsWith('Landscape:trees:') && name.endsWith(':crown')) treeCrowns++;
        });
        canvas.dataset.treeStyle = 'natural_trees_v1';
        canvas.dataset.treeCrowns = String(treeCrowns);
        water.forEach(node => node.traverse(child => {
          if (!(child instanceof Mesh)) return;
          (Array.isArray(child.material) ? child.material : [child.material]).forEach(material => {
            const value = material as MeshStandardMaterial;
            value.transparent = true; value.opacity = 0.68; value.depthWrite = false;
            value.roughness = 0.3; value.metalness = 0.05;
          });
          child.renderOrder = 2;
        }));
        root = gltf.scene;
        scene.add(root);
        bound.setFromObject(root);
        canvas.dataset.modelReady = 'true';
        applyVisibility(visibility); fit(view);
        options.onReady(); scheduler.invalidate();
      } catch (error) {
        console.error('River component binding failed.', error);
        disposeModel(gltf.scene); groupNodes.clear(); nodeGroups.clear(); options.onError();
      }
    },
  });
  return {
    visibility: applyVisibility,
    camera: fit,
    theme(theme) { renderer.setClearColor(new Color(themePalette[theme].canvasBackground)); scheduler.invalidate(); },
    label(label) { canvas.setAttribute('aria-label', label); },
    dispose() {
      if (disposed) return;
      disposed = true; load.cancel(); scheduler.dispose(); observer.disconnect(); intersection?.disconnect();
      document.removeEventListener('visibilitychange', documentVisibility);
      canvas.removeEventListener('webglcontextlost', lost);
      canvas.removeEventListener('pointerdown', down); canvas.removeEventListener('pointerup', up);
      controls.removeEventListener('change', changed); controls.dispose();
      if (root) disposeModel(root);
      sun.shadow.dispose();
      renderer.dispose(); canvas.remove();
    },
  };
}
