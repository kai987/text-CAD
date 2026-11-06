import { Box3, BufferGeometry, DirectionalLight, DoubleSide, Float32BufferAttribute, Group, HemisphereLight, Mesh, MeshBasicMaterial, OrthographicCamera, Raycaster, Scene, Vector2, Vector3, WebGLRenderer } from 'three';
import type { Material, Object3D } from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { modelAsset } from './data';
import { startModelLoad } from './model-resource';
import type { ModelProgress } from './model-resource';
import { bindCadNodes, isObjectVisible } from './model-scene';
import { createDemandRenderScheduler } from './demand-render';
import { bridgeGroupForName, bridgeGroups, bridgeRevision } from './bridge-copy';
import type { BridgeCamera, BridgeGroupId } from './bridge-copy';
import type { ResolvedTheme } from './theme-preferences';
import { themePalette } from './theme-preferences';
import { bridgeDisplay } from './bridge-batches';
import type { BridgeActorDisplay } from './bridge-batches';
import { bridgeActivityRunning, bridgeActorPose, createBridgeMotionClock, parseBridgeActivity } from './bridge-motion';
import type { BridgeActivity } from './bridge-motion';
import { bridgeWaterShaderProfile, createBridgeWater } from './bridge-water';

export interface BridgeViewer {
  visibility(values: Record<BridgeGroupId, boolean>): void;
  camera(mode: BridgeCamera): void;
  appearance(theme: ResolvedTheme, night: boolean): void;
  label(value: string): void;
  playing(value: boolean): void;
  waterWaves(value: boolean): void;
  dispose(): void;
}
function disposeModel(root: Object3D) {
  const materials = new Set<Material>(), geometries = new Set<BufferGeometry>();
  root.traverse(node => {
    if (!(node instanceof Mesh)) return;
    geometries.add(node.geometry);
    for (const material of Array.isArray(node.material) ? node.material : [node.material]) materials.add(material);
  });
  geometries.forEach(geometry => geometry.dispose()); materials.forEach(material => material.dispose());
}


export function createBridgeViewer(host: HTMLElement, options: {
  theme: ResolvedTheme; night: boolean; label: string; playing: boolean; waterWaves: boolean;
  onReady(): void; onError(error?: unknown): void; onProgress(value: ModelProgress): void; onSelection(value: BridgeGroupId | null): void;
}): BridgeViewer {
  const renderer = new WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, window.innerWidth <= 760 ? 1.5 : 2));
  const canvas = renderer.domElement;
  canvas.tabIndex = 0; canvas.setAttribute('role', 'img'); canvas.setAttribute('aria-label', options.label);
  canvas.dataset.renderStrategy = 'demand-and-activity'; canvas.dataset.modelId = 'seto-ohashi'; canvas.dataset.modelRevision = bridgeRevision;
  host.prepend(canvas);
  const scene = new Scene(), sky = new HemisphereLight(0xffffff, 0x667b8f, 2.5), sun = new DirectionalLight(0xfff3df, 3.1), fill = new DirectionalLight(0xc5e3ff, 1.4);
  sun.position.set(-1400, 2200, 1800); fill.position.set(1400, 1200, -1400); scene.add(sky, sun, fill);
  const camera = new OrthographicCamera(-1800, 1800, 500, -500, .1, 30000), controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true; controls.dampingFactor = .14; controls.zoomToCursor = true;
  controls.minZoom = .3; controls.maxZoom = 50; controls.maxPolarAngle = Math.PI * .91; controls.listenToKeyEvents(canvas);
  let root: Object3D | null = null, display: Group | null = null, disposed = false, inViewport = true, contextLost = false, frames = 0;
  let fitted = false;
  let mode: BridgeCamera = 'iso', fitHorizontal = 1600, fitVertical = 400;
  let theme = options.theme, night = options.night, playing = options.playing, waterWaves = options.waterWaves;
  let activity: BridgeActivity | null = null, actors = new Map<string, BridgeActorDisplay>();
  const clocks = { traffic: createBridgeMotionClock(), vessels: createBridgeMotionClock(), trains: createBridgeMotionClock(), water: createBridgeMotionClock() };
  let water: ReturnType<typeof createBridgeWater> | null = null;
  const wakes = new Map<string, Mesh>(), ownedMaterials = new Set<Material>();
  let following: BridgeActorDisplay | null = null, followPosition: Vector3 | null = null;
  const bounds = new Box3(), regions = new Map<BridgeCamera, Box3>();
  let groups = new Map<BridgeGroupId, Object3D[]>();
  let visibility = Object.fromEntries(bridgeGroups.map(id => [id, true])) as Record<BridgeGroupId, boolean>;
  const scheduler = createDemandRenderScheduler({
    draw() {
      availability();
      if (disposed || canvas.dataset.renderVisibility !== 'visible') return;
      animate(performance.now());
      controls.update(); renderer.render(scene, camera);
      if (motionRunning()) scheduler.invalidate();
      canvas.dataset.renderedFrames = String(++frames); canvas.dataset.renderCalls = String(renderer.info.render.calls);
      canvas.dataset.renderTriangles = String(renderer.info.render.triangles);
      canvas.dataset.cameraPose = JSON.stringify({ position: camera.position.toArray(), target: controls.target.toArray(), zoom: camera.zoom, verticalSpan: camera.top - camera.bottom });
    }, requestFrame: callback => requestAnimationFrame(callback), cancelFrame: id => cancelAnimationFrame(id),
    onState: value => { canvas.dataset.renderState = value; },
  });
  function availability() {
    const value = document.hidden ? 'document-hidden' : contextLost ? 'context-lost' : !host.clientWidth || !host.clientHeight ? 'layout-hidden' : !inViewport ? 'offscreen' : 'visible';
    canvas.dataset.renderVisibility = value;
    for (const group of ['traffic', 'vessels', 'trains'] as const) if (value !== 'visible' || !playing || !visibility[group]) clocks[group].pause();
    if (value !== 'visible' || !playing || !visibility.environment || !waterWaves) clocks.water.pause();
    const active = bridgeActivityRunning(playing, value === 'visible', visibility, visibility.environment, waterWaves);
    canvas.dataset.motionState = !activity ? 'loading' : value !== 'visible' ? 'hidden' : !playing ? 'paused' : active ? 'playing' : 'inactive-groups';
    canvas.dataset.waterWaves = String(waterWaves);
    scheduler.setActive(!disposed && value === 'visible');
  }
  function motionRunning() {
    return !!activity && !disposed && bridgeActivityRunning(playing, canvas.dataset.renderVisibility === 'visible', visibility, visibility.environment, waterWaves);
  }
  function animate(now: number) {
    if (!activity) return;
    const visible = canvas.dataset.renderVisibility === 'visible', times = {
      traffic: clocks.traffic.step(now, playing && visible && visibility.traffic),
      vessels: clocks.vessels.step(now, playing && visible && visibility.vessels),
      trains: clocks.trains.step(now, playing && visible && visibility.trains),
      water: clocks.water.step(now, playing && visible && visibility.environment && waterWaves),
    };
    water?.time(times.water);
    for (const { spec, object } of actors.values()) {
      const pose = bridgeActorPose(spec, activity, times[spec.group]); object.position.copy(pose.position); object.quaternion.copy(pose.rotation);
      const wake = wakes.get(spec.id);
      if (wake) { wake.position.set(pose.position.x, spec.origin_mm[2] / 1000 + .06, pose.position.z); wake.rotation.y = spec.heading_rad; }
    }
    if (following && followPosition) {
      const point = following.object.getWorldPosition(new Vector3());
      if (following.spec.group === 'vessels') point.y = followPosition.y;
      const difference = point.clone().sub(followPosition); camera.position.add(difference); controls.target.add(difference); followPosition.copy(point);
    }
    if (frames % 6 === 0 || !motionRunning()) {
      canvas.dataset.motionTimeTraffic = times.traffic.toFixed(3); canvas.dataset.motionTimeVessels = times.vessels.toFixed(3);
      canvas.dataset.motionTimeTrains = times.trains.toFixed(3); canvas.dataset.waterTime = times.water.toFixed(3);
      const samples: Record<string, number[]> = {};
      for (const group of ['traffic', 'vessels', 'trains']) {
        const actor = [...actors.values()].find(item => item.spec.group === group);
        if (actor) samples[group] = actor.object.position.toArray().map(value => Math.round(value * 1000) / 1000);
      }
      canvas.dataset.actorPoses = JSON.stringify(samples);
      canvas.dataset.trainPoses = JSON.stringify([...actors.values()].filter(actor => actor.spec.group === 'trains').map(actor => ({ id: actor.spec.id, train: actor.spec.train_id, index: actor.spec.carriage_index, position: actor.object.position.toArray() })));
    }
  }
  function addWakes() {
    if (!display) return;
    for (const { spec } of actors.values()) {
      if (spec.group !== 'vessels') continue;
      const length = spec.length_mm / 1000, width = spec.width_mm / 1000, positions: number[] = [];
      for (const sign of [-1, 1]) positions.push(-length * .35, 0, sign * width * .25, -length * 1.6, 0, sign * width * 1.65, -length * 1.6, 0, sign * width * 1.2);
      const geometry = new BufferGeometry(); geometry.setAttribute('position', new Float32BufferAttribute(positions, 3));
      const material = new MeshBasicMaterial({ color: '#e4f3ef', transparent: true, opacity: .24, side: DoubleSide, depthWrite: false });
      ownedMaterials.add(material);
      const wake = new Mesh(geometry, material); wake.name = 'vessels:' + spec.id + ':display_only_wake'; wake.userData.bridgeGroup = 'vessels';
      wake.position.set(spec.origin_mm[0] / 1000, spec.origin_mm[2] / 1000 + .06, -spec.origin_mm[1] / 1000); wake.rotation.y = spec.heading_rad;
      display.add(wake); wakes.set(spec.id, wake); groups.get('vessels')!.push(wake);
    }
  }
  function resize() {
    availability();
    if (disposed || !host.clientWidth || !host.clientHeight) return;
    const aspect = host.clientWidth / host.clientHeight, halfHeight = Math.max(fitVertical, fitHorizontal / aspect, .1) * 1.1;
    camera.left = -halfHeight * aspect; camera.right = halfHeight * aspect; camera.top = halfHeight; camera.bottom = -halfHeight;
    camera.updateProjectionMatrix(); renderer.setSize(host.clientWidth, host.clientHeight, false); scheduler.invalidate();
  }
  function fit(next: BridgeCamera) {
    mode = next;
    if (!root || !host.clientWidth || !host.clientHeight) return;
    following = ['traffic', 'vessel', 'train'].includes(next) ? [...actors.values()].find(actor => actor.spec.group === (next === 'traffic' ? 'traffic' : next === 'train' ? 'trains' : 'vessels')) ?? null : null;
    followPosition = following ? following.object.getWorldPosition(new Vector3()) : null;
    canvas.dataset.followingActor = following?.spec.id ?? '';
    let region = following ? new Box3().setFromObject(following.object) : (regions.get(next) ?? bounds).clone();
    if (following && next === 'train') {
      for (const actor of actors.values()) if (actor.spec.train_id === following.spec.train_id) region.expandByObject(actor.object);
      region.expandByVector(new Vector3(10, 5, 12));
    } else if (following) region.expandByVector(next === 'traffic' ? new Vector3(16, 6, 18) : new Vector3(22, 7, 18));
    const center = region.getCenter(new Vector3());
    const directions = { iso: new Vector3(1.1, .65, 1.8), elevation: new Vector3(0, 0, 2), top: new Vector3(0, 2, 0), tower: new Vector3(1, .35, 1.5), deck: new Vector3(.9, .35, 1.8), traffic: new Vector3(1.15, .8, 1.5), vessel: new Vector3(1.2, .7, 1.8), train: new Vector3(.45, .20, 1.8) };
    camera.up.set(0, next === 'top' ? 0 : 1, next === 'top' ? -1 : 0);
    controls.target.copy(center); camera.position.copy(center).addScaledVector(directions[next], 6000);
    camera.lookAt(center); camera.updateMatrixWorld(); fitHorizontal = 0; fitVertical = 0;
    for (const x of [region.min.x, region.max.x]) for (const y of [region.min.y, region.max.y]) for (const z of [region.min.z, region.max.z]) {
      const point = new Vector3(x, y, z).applyMatrix4(camera.matrixWorldInverse);
      fitHorizontal = Math.max(fitHorizontal, Math.abs(point.x)); fitVertical = Math.max(fitVertical, Math.abs(point.y));
    }
    camera.zoom = 1; controls.update(); resize(); fitted = true; canvas.dataset.cameraView = next;
  }
  function applyVisibility(values: Record<BridgeGroupId, boolean>) {
    visibility = { ...values };
    for (const [group, nodes] of groups) nodes.forEach(node => { node.visible = visibility[group] && !node.userData.bridgeWaterSource; });
    canvas.dataset.visibleGroups = JSON.stringify(bridgeGroups.filter(group => visibility[group])); availability(); scheduler.invalidate();
  }
  function appearance() {
    renderer.setClearColor(night ? '#091624' : themePalette[theme].canvasBackground);
    sky.intensity = night ? .9 : 2.5; sun.intensity = night ? .5 : 3.1; fill.intensity = night ? 1.25 : 1.4;
    water?.night(night); canvas.dataset.environment = night ? 'night' : 'day'; scheduler.invalidate();
  }
  const releaseFollow = () => { following = null; followPosition = null; canvas.dataset.followingActor = ''; };
  const keyNavigation = (event: KeyboardEvent) => { if (event.key.startsWith('Arrow')) releaseFollow(); };
  canvas.addEventListener('keydown', keyNavigation); controls.addEventListener('start', releaseFollow);
  const change = () => scheduler.invalidate(), observer = new ResizeObserver(() => {
    // Model loading also runs on a drawing entry; fit when its hidden canvas is first revealed.
    if (root && !fitted) fit(mode); else resize();
  });
  controls.addEventListener('change', change); observer.observe(host);
  const intersection = typeof IntersectionObserver === 'undefined' ? null : new IntersectionObserver(entries => { inViewport = entries.at(-1)?.isIntersecting ?? true; availability(); });
  intersection?.observe(host);
  const documentVisibility = () => availability(); document.addEventListener('visibilitychange', documentVisibility);
  const lost = (event: Event) => { event.preventDefault(); contextLost = true; availability(); options.onError(); };
  canvas.addEventListener('webglcontextlost', lost);
  let downPoint: { x: number; y: number } | null = null;
  const down = (event: PointerEvent) => { downPoint = { x: event.clientX, y: event.clientY }; };
  const up = (event: PointerEvent) => {
    if (!display || !downPoint || Math.hypot(event.clientX - downPoint.x, event.clientY - downPoint.y) > 5) { downPoint = null; return; }
    downPoint = null;
    const rect = canvas.getBoundingClientRect(), point = new Vector2((event.clientX - rect.left) / rect.width * 2 - 1, -(event.clientY - rect.top) / rect.height * 2 + 1);
    const ray = new Raycaster(); ray.setFromCamera(point, camera);
    const hit = ray.intersectObject(display, true).find(item => isObjectVisible(item.object));
    options.onSelection(hit?.object.userData.bridgeGroup ?? null);
  };
  canvas.addEventListener('pointerdown', down); canvas.addEventListener('pointerup', up);
  appearance(); resize();
  const loader = new GLTFLoader(), load = startModelLoad({
    ...modelAsset('GLB/seto_ohashi.glb'), parse: bytes => loader.parseAsync(bytes, ''), onProgress: options.onProgress,
    onError: options.onError, disposeLate: gltf => disposeModel(gltf.scene),
    onLoad(gltf) {
      try {
        bindCadNodes(gltf); root = gltf.scene; bounds.makeEmpty();
        activity = parseBridgeActivity(gltf.parser.json.asset?.extras?.activity);
        // Named south tower + adjoining span: the opposite bridge remains available in overview.
        const towerBounds = new Box3(), trussBounds = new Box3();
        root.traverse(node => {
          const name = String(node.userData.cadName ?? node.name);
          if (node instanceof Mesh && /^towers[:\-]south[:\-]tower_1[:\-]/.test(name)) towerBounds.expandByObject(node);
          if (node instanceof Mesh && bridgeGroupForName(name) === 'truss') trussBounds.expandByObject(node);
          if (node instanceof Mesh && bridgeGroupForName(name) && !['environment', 'traffic', 'vessels', 'trains'].includes(bridgeGroupForName(name)!)) bounds.expandByObject(node);
        });
        if (towerBounds.isEmpty() || trussBounds.isEmpty() || bounds.isEmpty()) throw new Error('Bridge camera regions are missing.');
        const southTowerX = towerBounds.getCenter(new Vector3()).x;
        regions.set('tower', towerBounds.clone().expandByVector(new Vector3(60, 10, 30)));
        regions.set('deck', new Box3(new Vector3(southTowerX + 65, trussBounds.min.y - 8, -28), new Vector3(southTowerX + 150, trussBounds.max.y + 8, 28)));
        const presentation = bridgeDisplay(root, activity); display = presentation.display; groups = presentation.groups; actors = presentation.actors;
        presentation.ownedMaterials.forEach(material => ownedMaterials.add(material));
        const seaBounds = new Box3();
        display.traverse(node => { if (node.userData.bridgeWaterSource) { seaBounds.expandByObject(node); node.visible = false; } });
        if (seaBounds.isEmpty()) throw new Error('Bridge sea surface is missing.');
        water = createBridgeWater(seaBounds); water.night(night); display.add(water.mesh); groups.get('environment')!.push(water.mesh);
        ownedMaterials.add(water.mesh.material); canvas.dataset.waterProfile = JSON.stringify(bridgeWaterShaderProfile);
        addWakes();
        display.applyMatrix4(root.matrixWorld); scene.add(display);
        canvas.dataset.modelReady = 'true'; canvas.dataset.drawBatches = String(presentation.batchCount);
        canvas.dataset.actorCount = String(actors.size);
        applyVisibility(visibility); fit(mode); options.onReady();
      } catch (error) {
        if (display) { scene.remove(display); display.traverse(node => { if (node instanceof Mesh) node.geometry.dispose(); }); display = null; }
        ownedMaterials.forEach(material => material.dispose()); ownedMaterials.clear(); wakes.clear(); actors.clear(); groups.clear(); water = null; activity = null;
        disposeModel(gltf.scene); root = null; delete canvas.dataset.modelReady; availability(); options.onError(error);
      }
    },
  });
  return {
    visibility: applyVisibility, camera: fit,
    appearance(value, nextNight) { theme = value; night = nextNight; appearance(); },
    label(value) { canvas.setAttribute('aria-label', value); },
    playing(value) { playing = value; Object.values(clocks).forEach(clock => clock.pause()); availability(); scheduler.invalidate(); },
    waterWaves(value) { waterWaves = value; clocks.water.pause(); availability(); scheduler.invalidate(); },
    dispose() {
      if (disposed) return;
      disposed = true; load.cancel(); scheduler.dispose(); observer.disconnect(); intersection?.disconnect();
      document.removeEventListener('visibilitychange', documentVisibility); canvas.removeEventListener('webglcontextlost', lost);
      canvas.removeEventListener('pointerdown', down); canvas.removeEventListener('pointerup', up); canvas.removeEventListener('keydown', keyNavigation); controls.removeEventListener('start', releaseFollow); controls.removeEventListener('change', change); controls.dispose();
      display?.traverse(node => { if (node instanceof Mesh) node.geometry.dispose(); });
      ownedMaterials.forEach(material => material.dispose());
      if (root) disposeModel(root); renderer.dispose(); canvas.remove();
    },
  };
}
