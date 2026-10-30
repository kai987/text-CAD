import { Box3, DirectionalLight, HemisphereLight, Mesh, OrthographicCamera, PointLight, Raycaster, Scene, SpotLight, Vector2, Vector3, WebGLRenderer } from 'three';
import type { Material, Object3D } from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { asset, assetSha256 } from './data';
import { bindCadNodes, isObjectVisible } from './model-scene';
import { createDemandRenderScheduler } from './demand-render';
import { startModelLoad } from './model-resource';
import type { ModelProgress } from './model-resource';
import type { ResolvedTheme } from './theme-preferences';
import { themePalette } from './theme-preferences';
import { landmarkGroupForName, landmarkGroupIds, landmarkModels } from './landmark-copy';
import type { LandmarkCamera, LandmarkGroupId, LandmarkId } from './landmark-copy';
import { bindLandmarkMaterialLighting, landmarkLocalLightLayout, landmarkLocalLightVisibility } from './landmark-lighting';
import type { LandmarkMaterialLighting } from './landmark-lighting';
import { batchLandmarkStairs } from './landmark-stair-batches';
import type { LandmarkStairBatches } from './landmark-stair-batches';
import { batchSkytreeOpaque } from './skytree-opaque-batches';
import type { SkytreeOpaqueBatches } from './skytree-opaque-batches';
import { landmarkCloseupBounds } from './landmark-camera-bounds';
import { bindLandmarkSteelDetails, readLandmarkSteelNodes } from './landmark-steel-nodes';
import type { LandmarkSteelDetails, LandmarkSteelNode, SteelMicroMode } from './landmark-steel-nodes';

export interface LandmarkViewer {
  visibility(values: Record<LandmarkGroupId, boolean>): void;
  camera(mode: LandmarkCamera): void;
  steelNode(id: string): void;
  steelMicro(mode: SteelMicroMode): void;
  appearance(theme: ResolvedTheme, night: boolean): void;
  label(value: string): void;
  dispose(): void;
}
function disposeModel(root: Object3D) {
  const materials = new Set<Material>(), geometries = new Set<Mesh['geometry']>();
  root.traverse(node => {
    if (!(node instanceof Mesh)) return;
    geometries.add(node.geometry);
    for (const material of Array.isArray(node.material) ? node.material : [node.material]) materials.add(material);
  });
  geometries.forEach(geometry => geometry.dispose()); materials.forEach(material => material.dispose());
}

export function createLandmarkViewer(host: HTMLElement, id: LandmarkId, options: {
  theme: ResolvedTheme; night: boolean; label: string;
  onReady(): void; onError(): void; onProgress(value: ModelProgress): void; onSelection(value: LandmarkGroupId | null): void;
  onSteelNodes(value: readonly LandmarkSteelNode[]): void;
  onSteelNodeSelection?(value: string): void;
}): LandmarkViewer {
  const renderer = new WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, window.innerWidth <= 760 ? 1.5 : 2));
  const canvas = renderer.domElement;
  canvas.tabIndex = 0; canvas.setAttribute('role', 'img'); canvas.setAttribute('aria-label', options.label);
  canvas.dataset.renderStrategy = 'demand'; canvas.dataset.modelId = id;
  host.prepend(canvas);
  const scene = new Scene();
  const sky = new HemisphereLight(0xffffff, 0x667b8f, 2.7);
  const sun = new DirectionalLight(0xfff1db, 3.1);
  const fill = new DirectionalLight(0xc5e3ff, 1.5);
  const height = landmarkModels[id].height / 1000;
  sun.position.set(-height, height * 1.8, height); fill.position.set(height, height, -height);
  scene.add(sky, sun, fill);
  // A bounded light rig covers each tower without one source per lens.
  // Positions and intensity are appearance assumptions, not a lighting design.
  const localLights = landmarkLocalLightLayout(id).map(spec => {
    const light = spec.kind === 'spot'
      ? new SpotLight(spec.color, spec.intensity, spec.distance, Math.PI / 8, .65, 2)
      : new PointLight(spec.color, spec.intensity, spec.distance, 2);
    light.position.fromArray(spec.position); light.visible = false; scene.add(light);
    if (light instanceof SpotLight && spec.target) { light.target.position.fromArray(spec.target); scene.add(light.target); }
    return { light, channel: spec.channel };
  });
  const camera = new OrthographicCamera(-height, height, height, -height, .1, height * 12);
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true; controls.dampingFactor = .14; controls.zoomToCursor = true;
  controls.minZoom = .3; controls.maxZoom = 32; controls.maxPolarAngle = Math.PI * .94;
  controls.listenToKeyEvents(canvas);
  let root: Object3D | null = null, disposed = false, inViewport = true, contextLost = false, frames = 0;
  let fitHorizontal = height / 2, fitVertical = height / 2;
  let mode: LandmarkCamera = 'iso';
  let theme = options.theme, night = options.night;
  const bounds = new Box3();
  const closeupBounds = new Map<LandmarkCamera, Box3>();
  const groups = new Map<LandmarkGroupId, Object3D[]>();
  let materialLighting: LandmarkMaterialLighting | null = null;
  let stairBatches: LandmarkStairBatches | null = null;
  let skytreeOpaqueBatches: SkytreeOpaqueBatches | null = null;
  let steelDetails: LandmarkSteelDetails | null = null;
  let steelMicroMode: SteelMicroMode = 'auto', steelNodeId: string | null = null;
  let visibility = Object.fromEntries(landmarkGroupIds.map(group => [group, true])) as Record<LandmarkGroupId, boolean>;
  const scheduler = createDemandRenderScheduler({
    draw() {
      availability();
      if (disposed || canvas.dataset.renderVisibility !== 'visible') return;
      controls.update(); updateSteelDetails(); renderer.render(scene, camera);
      canvas.dataset.renderedFrames = String(++frames);
      canvas.dataset.renderTriangles = String(renderer.info.render.triangles);
      canvas.dataset.cameraPose = JSON.stringify({ position: camera.position.toArray(), target: controls.target.toArray(), zoom: camera.zoom });
    },
    requestFrame: callback => requestAnimationFrame(callback), cancelFrame: frame => cancelAnimationFrame(frame),
    onState: value => { canvas.dataset.renderState = value; },
  });
  function availability() {
    const value = document.hidden ? 'document-hidden' : contextLost ? 'context-lost' : !host.clientWidth || !host.clientHeight ? 'layout-hidden' : !inViewport ? 'offscreen' : 'visible';
    canvas.dataset.renderVisibility = value; scheduler.setActive(!disposed && value === 'visible');
  }
  function resize() {
    availability();
    if (disposed || !host.clientWidth || !host.clientHeight) return;
    const aspect = host.clientWidth / host.clientHeight;
    const halfHeight = Math.max(fitVertical, fitHorizontal / aspect, .1) * 1.12;
    camera.left = -halfHeight * aspect; camera.right = halfHeight * aspect;
    camera.top = halfHeight; camera.bottom = -halfHeight; camera.updateProjectionMatrix();
    renderer.setSize(host.clientWidth, host.clientHeight, false); scheduler.invalidate();
  }
  function fit(next: LandmarkCamera) {
    mode = next;
    if (!root || !host.clientWidth || !host.clientHeight) return;
    const region = closeupBounds.get(next) ?? bounds;
    const center = region.getCenter(new Vector3());
    const directions = { iso: new Vector3(1, 1, 1), front: new Vector3(0, 0, 2), side: new Vector3(2, 0, 0), top: new Vector3(0, 2, 0), base: new Vector3(1, .6, 1), 'main-deck': new Vector3(1, .38, 1), 'top-deck': new Vector3(1, .3, 1), 'tembo-deck': new Vector3(1, .3, 1), 'tembo-galleria': new Vector3(1, .25, 1), spire: new Vector3(1, .2, 1), 'steel-node': steelDetails?.direction(steelNodeId ?? '') ?? new Vector3(1, .4, 1) };
    camera.up.set(0, next === 'top' ? 0 : 1, next === 'top' ? -1 : 0);
    controls.target.copy(center); camera.position.copy(center).addScaledVector(directions[next], height * 2);
    camera.lookAt(center); camera.updateMatrixWorld();
    fitHorizontal = 0; fitVertical = 0;
    for (const x of [region.min.x, region.max.x]) for (const y of [region.min.y, region.max.y]) for (const z of [region.min.z, region.max.z]) {
      const p = new Vector3(x, y, z).applyMatrix4(camera.matrixWorldInverse);
      fitHorizontal = Math.max(fitHorizontal, Math.abs(p.x)); fitVertical = Math.max(fitVertical, Math.abs(p.y));
    }
    camera.zoom = 1; controls.update(); resize(); canvas.dataset.cameraView = next;
  }
  function applyVisibility(values: Record<LandmarkGroupId, boolean>) {
    visibility = { ...values };
    for (const [group, nodes] of groups) for (const node of nodes) node.visible = visibility[group];
    canvas.dataset.visibleGroups = JSON.stringify(landmarkGroupIds.filter(group => visibility[group]));
    updateLocalLighting();
    scheduler.invalidate();
  }
  function updateLocalLighting() {
    const local = landmarkLocalLightVisibility(id, night, visibility, !!root);
    for (const { light, channel } of localLights) light.visible = local[channel];
    const stats = materialLighting?.apply(night);
    canvas.dataset.lightMode = 'local-fixtures';
    canvas.dataset.activeLocalLights = String(localLights.filter(({ light }) => light.visible).length);
    if (stats) canvas.dataset.lightingStats = JSON.stringify(stats);
  }
  function updateSteelDetails() {
    const stats = steelDetails?.apply(camera, steelMicroMode);
    canvas.dataset.steelMicroMode = steelMicroMode;
    if (stats) { canvas.dataset.steelMicroMeshes = String(stats.microMeshes); canvas.dataset.visibleSteelMicroMeshes = String(stats.visibleMicroMeshes); }
  }
  function focusSteelNode(id: string) {
    const region = steelDetails?.bounds(id);
    if (!region) return;
    steelNodeId = id; closeupBounds.set('steel-node', region); canvas.dataset.steelNode = id; fit('steel-node');
  }
  function appearance(nextTheme: ResolvedTheme, nextNight: boolean) {
    theme = nextTheme; night = nextNight;
    renderer.setClearColor(night ? '#0b1728' : themePalette[theme].canvasBackground);
    // The pale Skytree frame needs lower daylight exposure to retain its
    // section shading against the light CAD canvas. Tokyo keeps its settings.
    const skytree = id === 'tokyo-skytree';
    sky.intensity = night ? .65 : skytree ? 1.65 : 2.7;
    sun.intensity = night ? skytree ? .7 : .95 : skytree ? 2.1 : 3.1;
    fill.intensity = night ? skytree ? .95 : .85 : skytree ? .8 : 1.1;
    updateLocalLighting();
    canvas.dataset.environment = night ? 'night' : 'day'; scheduler.invalidate();
  }
  const changed = () => scheduler.invalidate();
  controls.addEventListener('change', changed);
  const observer = new ResizeObserver(() => { if (root && !frames) fit(mode); else resize(); }); observer.observe(host);
  const intersection = typeof IntersectionObserver === 'undefined' ? null : new IntersectionObserver(entries => {
    inViewport = entries.at(-1)?.isIntersecting ?? true; availability();
  }); intersection?.observe(host);
  const documentVisibility = () => availability(); document.addEventListener('visibilitychange', documentVisibility);
  const lost = (event: Event) => { event.preventDefault(); contextLost = true; availability(); options.onError(); };
  canvas.addEventListener('webglcontextlost', lost);
  let downPoint: Vector2 | null = null;
  const down = (event: PointerEvent) => { downPoint = new Vector2(event.clientX, event.clientY); };
  const up = (event: PointerEvent) => {
    if (!downPoint || !root || downPoint.distanceTo(new Vector2(event.clientX, event.clientY)) > 5) { downPoint = null; return; }
    downPoint = null;
    const rect = canvas.getBoundingClientRect();
    const point = new Vector2((event.clientX - rect.left) / rect.width * 2 - 1, -(event.clientY - rect.top) / rect.height * 2 + 1);
    const ray = new Raycaster(); ray.setFromCamera(point, camera);
    for (const hit of ray.intersectObject(root, true)) {
      if (!isObjectVisible(hit.object)) continue;
      const nodeId = hit.object.userData.steelNodeId;
      if (typeof nodeId === 'string' && steelDetails?.catalog.some(entry => entry.id === nodeId)) options.onSteelNodeSelection?.(nodeId);
      for (let node: Object3D | null = hit.object; node; node = node.parent) {
        const group = landmarkGroupForName(String(node.userData.cadName ?? node.name));
        if (group) { options.onSelection(group); return; }
      }
    }
    options.onSelection(null);
  };
  canvas.addEventListener('pointerdown', down); canvas.addEventListener('pointerup', up);
  appearance(theme, night); resize();
  const path = `GLB/${landmarkModels[id].stem}.glb`;
  const loader = new GLTFLoader();
  const load = startModelLoad({
    url: asset(path), compressed: !!assetSha256(`${path}.gz`), compressedUrl: asset(`${path}.gz`), expectedSha256: assetSha256(path),
    parse: bytes => loader.parseAsync(bytes, ''), onProgress: options.onProgress,
    onError(error) { console.error('Landmark model load failed.', error); options.onError(); }, disposeLate: gltf => disposeModel(gltf.scene),
    onLoad(gltf) {
      try {
        const extras = gltf.parser.json.asset?.extras;
        if (extras?.landmarkId !== id || extras?.revision !== landmarkModels[id].revision) {
          throw new Error('The landmark model does not match this revision.');
        }
        const cadNodes = bindCadNodes(gltf);
        for (const group of landmarkGroupIds) {
          const node = cadNodes.get(group);
          if (!node) throw new Error(`Missing landmark component group: ${group}`);
          groups.set(group, [node]);
        }
        if (id === 'tokyo-tower') {
          const catalog = readLandmarkSteelNodes(extras.steelNodes);
          if (catalog.length !== 20) throw new Error('This tower requires its 20-node steel catalog.');
          steelDetails = bindLandmarkSteelDetails(cadNodes, catalog, gltf.scene);
          canvas.dataset.steelNodeCount = String(catalog.length); options.onSteelNodes(catalog);
        } else options.onSteelNodes([]);
        stairBatches = batchLandmarkStairs(gltf.scene, id);
        canvas.dataset.batchedStairMeshes = String(stairBatches.sourceMeshes);
        canvas.dataset.stairDrawBatches = String(stairBatches.drawBatches);
        materialLighting = bindLandmarkMaterialLighting(gltf.scene, id);
        root = gltf.scene; scene.add(root); bounds.setFromObject(root);
        if (bounds.isEmpty()) throw new Error('Empty landmark model.');
        for (const [preset, region] of landmarkCloseupBounds(id, cadNodes, bounds)) closeupBounds.set(preset, region);
        // Native bounds and the original named-node catalog stay authoritative.
        skytreeOpaqueBatches = batchSkytreeOpaque(root, id);
        canvas.dataset.opaqueBatchSourceMeshes = String(skytreeOpaqueBatches.sourceMeshes);
        canvas.dataset.opaqueDrawBatches = String(skytreeOpaqueBatches.drawBatches);
        canvas.dataset.modelRevision = extras.revision;
        canvas.dataset.modelReady = 'true'; canvas.dataset.modelHeight = String(bounds.max.y - bounds.min.y);
        applyVisibility(visibility); appearance(theme, night); fit(mode); options.onReady(); scheduler.invalidate();
      } catch (error) {
        console.error('Landmark component binding failed.', error);
        scene.remove(gltf.scene); root = null; materialLighting?.dispose(); materialLighting = null;
        steelDetails?.dispose(); steelDetails = null;
        skytreeOpaqueBatches?.dispose(); skytreeOpaqueBatches = null;
        stairBatches?.dispose(); stairBatches = null;
        disposeModel(gltf.scene); groups.clear(); closeupBounds.clear(); options.onError();
      }
    },
  });
  return {
    visibility: applyVisibility, camera: fit, appearance, steelNode: focusSteelNode,
    steelMicro(value) { steelMicroMode = value; scheduler.invalidate(); },
    label(value) { canvas.setAttribute('aria-label', value); },
    dispose() {
      if (disposed) return;
      disposed = true; load.cancel(); scheduler.dispose(); observer.disconnect(); intersection?.disconnect();
      document.removeEventListener('visibilitychange', documentVisibility); canvas.removeEventListener('webglcontextlost', lost);
      canvas.removeEventListener('pointerdown', down); canvas.removeEventListener('pointerup', up);
      controls.removeEventListener('change', changed); controls.dispose();
      materialLighting?.dispose(); materialLighting = null;
      steelDetails?.dispose(); steelDetails = null;
      skytreeOpaqueBatches?.dispose(); skytreeOpaqueBatches = null;
      stairBatches?.dispose(); stairBatches = null;
      if (root) disposeModel(root);
      for (const { light } of localLights) {
        scene.remove(light); if (light instanceof SpotLight) scene.remove(light.target); light.shadow.dispose();
      }
      closeupBounds.clear(); renderer.dispose(); canvas.remove();
    },
  };
}
