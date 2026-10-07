import {
  ACESFilmicToneMapping, Box3, BufferAttribute, BufferGeometry, Color, DirectionalLight, DoubleSide, EdgesGeometry, FrontSide, HemisphereLight, LineBasicMaterial,
  LineSegments, Mesh, Object3D, OrthographicCamera, Plane, PMREMGenerator, Raycaster, Scene, Texture, Vector2, Vector3, WebGLRenderer,
  NoToneMapping, PCFShadowMap,
} from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import type { GLTF } from 'three/addons/loaders/GLTFLoader.js';
import { startModelLoad } from './model-resource';
import type { ModelProgress } from './model-resource';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import type { Material, MeshStandardMaterial } from 'three';
import { asset } from './data';
import { modelLayouts, settingsForPreset } from './model-state';
import type { ModelLayout, ModelPartId, ModelSettings } from './model-state';
import { bindCadNodes, centerModelAtFloorDatum, isObjectVisible, selectionFor, visibleMeshes } from './model-scene';
import type { ModelSelection } from './model-scene';
import { createHorizontalCap, createSectionMaterial } from './section-caps';
import { createCadOutlineGeometry } from './cad-outlines';
import { themePalette } from './theme-preferences';
import type { ResolvedTheme } from './theme-preferences';
import { structuralObjectVisible } from './structural-design';
import type { StructuralOverlayState, StructuralSystem } from './structural-design';
import { createOutdoorLighting, nightScenePalette } from './scene-lighting';
import { createGeometryWorkerClient } from './geometry-worker-client';

export interface ViewerCameraState { mode: 'iso' | 'top'; position: number[]; target: number[]; up: number[]; zoom: number }

export interface HouseViewer {
  captureCamera: () => ViewerCameraState | null;
  restoreCamera: (state: ViewerCameraState) => void;
  apply: (settings: ModelSettings, selectionName?: string | null) => void;
  camera: (mode: 'iso' | 'top') => void;
  select: (name: string | null) => void;
  setTheme: (theme: ResolvedTheme) => void;
  setStructure: (system: StructuralSystem | null) => void;
  dispose: () => void;
}

function disposeObject(root: Object3D, disposeTextures = false) {
  const materials = new Set<Material>();
  root.traverse(o => {
    if (o instanceof Mesh || o instanceof LineSegments) {
      o.geometry.dispose();
      (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => materials.add(m));
    }
  });
  if (disposeTextures) {
    const textures = new Set<Texture>();
    materials.forEach(m => Object.values(m).forEach(value => { if (value instanceof Texture) textures.add(value); }));
    textures.forEach(texture => texture.dispose());
  }
  materials.forEach(m => m.dispose());
}

export function createHouseViewer(host: HTMLElement, onReady: () => void, onError: () => void,
  onSelection: (selection: ModelSelection | null) => void, initialTheme: ResolvedTheme = 'light',
  layout: ModelLayout = modelLayouts.house, glbPath = 'GLB/house_3d.glb',
  onOverlayState: (state: StructuralOverlayState) => void = () => {},
  onProgress: (progress: ModelProgress) => void = () => {},
  onContextRestored: () => void = () => {}): HouseViewer {
  let theme = initialTheme;
  const outlineMaterials = new Set<LineBasicMaterial>();
  function createOutlineMaterial(opacity = 0.55) {
    const material = new LineBasicMaterial({
      color: new Color(settings.environment === 'night' ? nightScenePalette.outline : themePalette[theme].outline),
      transparent: true, opacity: settings.environment === 'night' ? opacity * 0.48 : opacity,
    });
    material.userData.dayOpacity = opacity;
    outlineMaterials.add(material);
    return material;
  }
  const renderer = new WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(themePalette[theme].canvasBackground);
  renderer.domElement.tabIndex = 0;
  renderer.domElement.setAttribute('aria-label', '可旋转和缩放的房屋三维模型');
  renderer.domElement.setAttribute('role', 'img');
  const useTypeScript = new URLSearchParams(location.search).get('section') === 'typescript';
  renderer.domElement.dataset.sectionBackend = useTypeScript ? 'typescript' : 'loading-rust-worker';
  renderer.domElement.dataset.outlineBackend = useTypeScript ? 'typescript' : 'loading-rust-worker';
  host.prepend(renderer.domElement);
  const scene = new Scene();
  // Local studio lighting gives ceramic, glass and metal highlights without a remote HDR asset.
  const studio = new RoomEnvironment();
  const pmrem = new PMREMGenerator(renderer);
  const environment = pmrem.fromScene(studio, 0.04);
  scene.environment = environment.texture;
  scene.environmentIntensity = 0.12;
  studio.dispose(); pmrem.dispose();
  const sky = new HemisphereLight(0xffffff, 0xbac2cc, 1.8); scene.add(sky);
  const sun = new DirectionalLight(0xffffff, 2.0);
  sun.position.set(-8, 16, 12); scene.add(sun);
  const outdoorLighting = createOutdoorLighting(scene);
  renderer.shadowMap.type = PCFShadowMap;
  renderer.shadowMap.autoUpdate = false;
  const camera = new OrthographicCamera(-8, 8, 8, -8, 0.1, 100);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.12;
  controls.minZoom = 0.15; controls.maxZoom = 12;
  controls.maxPolarAngle = Math.PI * 0.94;
  controls.listenToKeyEvents(renderer.domElement);
  let disposed = false;
  let contextUnavailable = false;
  let frame = 0;
  let root: Object3D | undefined;
  let settings = settingsForPreset(layout.defaultPreset, layout);
  const groupObjects = new Map<ModelPartId, Object3D>();
  let cadObjects = new Map<string, Object3D>();
  let baselineCadObjects = new Map<string, Object3D>();
  const overlays = new Map<StructuralSystem, { root: Object3D; objects: Map<string, Object3D> }>();
  const overlayLoads = new Map<StructuralSystem, Promise<void>>();
  let structuralSystem: StructuralSystem | null = null;
  const originalMaterials = new Map<Mesh, Material | Material[]>();
  const sourceMeshes: Mesh[] = [];
  const sectionCaps = new Map<Mesh, Mesh>();
  let capHeight: number | null = null;
  let geometryWorker: ReturnType<typeof createGeometryWorkerClient> | null = null;
  let workerReady = false;
  let capGeneration = 0;
  const wallOutlines = new Map<Mesh, LineSegments | null>();
  const pendingOutlines = new Set<Mesh>();
  let selectedName: string | null = null;
  let halfHeight = 7;
  let mode: 'iso' | 'top' = 'iso';
  let cameraInitialized = false;
  function draw() {
    frame = 0;
    if (disposed || contextUnavailable || !host.clientWidth || !host.clientHeight) return;
    controls.update(); renderer.render(scene, camera);
    renderer.domElement.dataset.cameraPose = JSON.stringify({ position: camera.position.toArray(), target: controls.target.toArray(), zoom: camera.zoom });
  }
  function requestRender() { if (!disposed && !frame) frame = requestAnimationFrame(draw); }
  function setTheme(next: ResolvedTheme) {
    if (disposed) return;
    theme = next;
    updateEnvironment();
    requestRender();
  }
  function updateEnvironment() {
    const night = settings.environment === 'night';
    renderer.setClearColor(night ? nightScenePalette.background : themePalette[theme].canvasBackground);
    outlineMaterials.forEach(material => {
      material.color.set(night ? nightScenePalette.outline : themePalette[theme].outline);
      material.opacity = Number(material.userData.dayOpacity ?? 0.55) * (night ? 0.48 : 1);
    });
    sky.color.set(night ? nightScenePalette.sky : 0xffffff);
    sky.groundColor.set(night ? nightScenePalette.ground : 0xbac2cc);
    sky.intensity = night ? 0.48 : 1.8;
    sun.color.set(night ? nightScenePalette.moon : 0xffffff);
    sun.intensity = night ? 0.32 : 2;
    scene.environmentIntensity = night ? 0.035 : 0.12;
    renderer.toneMapping = night ? ACESFilmicToneMapping : NoToneMapping;
    renderer.toneMappingExposure = night ? 1.1 : 1;
    const lighting = outdoorLighting.update(settings);
    renderer.shadowMap.enabled = night && lighting.shadowLights > 0;
    renderer.shadowMap.needsUpdate = true;
    renderer.domElement.dataset.sceneEnvironment = settings.environment;
    renderer.domElement.dataset.outdoorLights = String(settings.outdoorLights);
    renderer.domElement.dataset.outdoorLightFixtures = String(lighting.total);
    renderer.domElement.dataset.activeOutdoorLights = String(lighting.active);
    renderer.domElement.dataset.activeOutdoorLightIds = JSON.stringify(lighting.activeIds);
    renderer.domElement.dataset.outdoorShadowLights = String(lighting.shadowLights);
  }
  controls.addEventListener('change', requestRender);
  function resize() {
    const width = host.clientWidth, height = host.clientHeight;
    if (!width || !height || disposed) return;
    renderer.setSize(width, height, false);
    camera.left = -halfHeight * width / height; camera.right = -camera.left;
    camera.top = halfHeight; camera.bottom = -halfHeight;
    camera.updateProjectionMatrix(); requestRender();
  }
  // Text reflow can resize the canvas during a language change. Adjust its framing
  // without resetting the user's orbit, pan or zoom.
  const observer = new ResizeObserver(() => { if (root) updateFrustum(); else resize(); }); observer.observe(host);
  function clearHighlight() {
    for (const [mesh, original] of originalMaterials) {
      (Array.isArray(mesh.material) ? mesh.material : [mesh.material]).forEach(material => material.dispose());
      mesh.material = original;
    }
    originalMaterials.clear();
  }
  function select(name: string | null) {
    clearHighlight(); selectedName = name;
    const target = name ? cadObjects.get(name) : undefined;
    if (target) for (const mesh of visibleMeshes(target)) {
      originalMaterials.set(mesh, mesh.material);
      const highlight = (material: Material) => {
        const copy = material.clone() as MeshStandardMaterial;
        if (copy.color) copy.color.set('#e7aa37');
        if (copy.emissive) { copy.emissive.set('#80520d'); copy.emissiveIntensity = 0.25; }
        return copy;
      };
      mesh.material = Array.isArray(mesh.material) ? mesh.material.map(highlight) : highlight(mesh.material);
    }
    requestRender();
  }
  function clearSectionCaps() {
    for (const [mesh, cap] of sectionCaps) {
      cap.traverse(object => {
        if (!(object instanceof LineSegments)) return;
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        materials.forEach(material => {
          if (material instanceof LineBasicMaterial) outlineMaterials.delete(material);
        });
      });
      mesh.remove(cap); disposeObject(cap);
    }
    sectionCaps.clear();
    renderer.domElement.dataset.sectionCapCount = '0';
  }
  function addSectionCap(mesh: Mesh, geometry: BufferGeometry) {
    const material = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
    const cap = new Mesh(geometry, createSectionMaterial(material));
    cap.name = `${mesh.name}_section_cap`;
    cap.userData.cadName = mesh.userData.cadName;
    cap.userData.sectionCap = true;
    cap.add(new LineSegments(new EdgesGeometry(geometry, 28), createOutlineMaterial()));
    mesh.add(cap); sectionCaps.set(mesh, cap);
  }
  function updateSectionCaps(height: number | null) {
    if (!root || height === capHeight) return;
    capHeight = height;
    const generation = ++capGeneration;
    geometryWorker?.cancelSections();
    clearSectionCaps();
    renderer.domElement.dataset.sectionPending = String(height !== null && !useTypeScript && !geometryWorker?.failed);
    renderer.domElement.dataset.sectionHeightMm = height === null ? '' : String(Math.round(height * 1000));
    if (height === null) return;
    root.updateWorldMatrix(true, true);
    const meshes = sourceMeshes.filter(mesh => {
      const material = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
      return !material.transparent && material.opacity >= 1;
    });
    if (!useTypeScript && geometryWorker && !geometryWorker.failed) {
      // Initialization runs alongside the GLB download. A ready/failure callback
      // rebuilds the current height; no geometry work runs on the UI thread here.
      if (!workerReady) return;
      const byId = new Map(meshes.map(mesh => [mesh.uuid, mesh]));
      const jobs = meshes.flatMap(mesh => {
        if (disposed || generation !== capGeneration) return [];
        const geometryId = geometryWorker!.registerGeometry(mesh.geometry);
        // A failed upload can synchronously invoke onFailure and rebuild all
        // caps via TypeScript. Do not append duplicates from this old batch.
        if (disposed || generation !== capGeneration) return [];
        if (!geometryId) {
          const geometry = createHorizontalCap(mesh, height - 0.00005);
          if (geometry) addSectionCap(mesh, geometry);
          return [];
        }
        return [{ id: mesh.uuid, geometryId, matrix: [...mesh.matrixWorld.elements], height: height - 0.00005 }];
      });
      if (disposed || generation !== capGeneration) return;
      void geometryWorker.sectionCaps(jobs).then(results => {
        // Height changes, structure changes and disposal all invalidate results.
        if (disposed || generation !== capGeneration || height !== capHeight || !results) return;
        clearHighlight();
        for (const result of results) {
          const mesh = byId.get(result.id);
          if (!mesh || !result.positions.length) continue;
          const geometry = new BufferGeometry();
          geometry.setAttribute('position', new BufferAttribute(result.positions, 3));
          geometry.setAttribute('normal', new BufferAttribute(result.normals, 3));
          geometry.computeBoundingBox(); geometry.computeBoundingSphere();
          addSectionCap(mesh, geometry);
        }
        renderer.domElement.dataset.sectionPending = 'false';
        renderer.domElement.dataset.sectionCapCount = String(sectionCaps.size);
        select(selectedName); requestRender();
      });
      return;
    }
    for (const mesh of meshes) {
      // Place the display-only cap 0.05 mm below the plane to avoid GPU clip round-off.
      const geometry = createHorizontalCap(mesh, height - 0.00005);
      if (geometry) addSectionCap(mesh, geometry);
    }
    renderer.domElement.dataset.sectionPending = 'false';
    renderer.domElement.dataset.sectionCapCount = String(sectionCaps.size);
  }
  function fit() {
    if (!root) return;
    root.updateWorldMatrix(true, true);
    const bounds = new Box3();
    root.traverse(o => { if (o instanceof Mesh && isObjectVisible(o)) bounds.expandByObject(o); });
    if (bounds.isEmpty()) return;
    cameraInitialized = true;
    const center = bounds.getCenter(new Vector3());
    controls.target.copy(center);
    if (mode === 'top') {
      camera.up.set(0, 0, -1); camera.position.copy(center).add(new Vector3(0, 30, 0.0001));
    } else {
      camera.up.set(0, 1, 0); camera.position.copy(center).add(new Vector3(18, 16, 18));
    }
    camera.lookAt(center); camera.zoom = 1; camera.updateMatrixWorld(true);
    controls.update(); updateFrustum();
  }
  function updateFrustum() {
    // The retained viewer has no layout while a plan is active. Reframe on reveal.
    if (!root || !host.clientWidth || !host.clientHeight) return;
    camera.updateMatrixWorld(true);
    const point = new Vector3();
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    root.traverse(o => {
      if (!(o instanceof Mesh) || !isObjectVisible(o)) return;
      const positions = o.geometry.getAttribute('position');
      for (let i = 0; i < positions.count; i++) {
        point.fromBufferAttribute(positions, i).applyMatrix4(o.matrixWorld).applyMatrix4(camera.matrixWorldInverse);
        minX = Math.min(minX, point.x); maxX = Math.max(maxX, point.x);
        minY = Math.min(minY, point.y); maxY = Math.max(maxY, point.y);
      }
    });
    if (![minX, minY, maxX, maxY].every(Number.isFinite)) { resize(); return; }
    const aspect = Math.max(host.clientWidth / Math.max(host.clientHeight, 1), 0.1);
    halfHeight = Math.max((maxY - minY) / 2, (maxX - minX) / (2 * aspect)) * 1.3;
    resize();
  }
  function apply(next: ModelSettings, selectionName = selectedName) {
    // Return temporary highlight materials before replacing any section geometry.
    clearHighlight();
    settings = next;
    layout.groups.forEach(g => { const part = groupObjects.get(g.id); if (part) part.visible = !!next.visibility[g.id]; });
    layout.parts.forEach(p => { const part = groupObjects.get(p.id); if (part) part.visible = !!next.partVisibility[p.id]; });
    // The independent frame and its foundation replace both original proposal groups.
    // Keep this intent when cutaway and individual-category controls make a custom view.
    if (structuralSystem) {
      for (const id of ['structure', 'foundation'] as const) {
        const original = groupObjects.get(id); if (original) original.visible = false;
      }
    }
    for (const [system, overlay] of overlays) {
      overlay.root.visible = system === structuralSystem;
      for (const part of [...layout.groups, ...layout.parts]) {
        if (!part.id.startsWith('structure') && !part.id.startsWith('foundation')) continue;
        const object = overlay.objects.get(part.id);
        if (object) object.visible = structuralObjectVisible(part.id, next);
      }
    }
    const currentOverlay = structuralSystem ? overlays.get(structuralSystem) : undefined;
    renderer.domElement.dataset.structureMeshes = String(currentOverlay ? visibleMeshes(currentOverlay.root).length : 0);
    renderer.domElement.dataset.baseFoundationHidden = String(structuralSystem !== null && groupObjects.get('foundation')?.visible === false);
    // GLB is Y-up/metres; display the cut height relative to the original F1 datum.
    const height = next.cutaway ? next.heightMm / 1000 : null;
    renderer.clippingPlanes = height === null ? [] : [new Plane(new Vector3(0, -1, 0), height)];
    updateSectionCaps(height);
    updateEnvironment();
    if (selectionName) {
      const target = cadObjects.get(selectionName);
      if (!target || !visibleMeshes(target).length) { select(null); onSelection(null); }
      else select(selectionName);
    } else select(null);
    requestRender();
  }
  function prepareMeshes(object: Object3D) {
    object.traverse(o => {
      if (!(o instanceof Mesh)) return;
      sourceMeshes.push(o);
      const materials = Array.isArray(o.material) ? o.material : [o.material];
      materials.forEach(m => {
        m.side = m.transparent ? DoubleSide : FrontSide;
        m.polygonOffset = true; m.polygonOffsetFactor = 1; m.polygonOffsetUnits = 1;
      });
      o.castShadow = materials.some(material => !material.transparent && material.opacity >= 1);
      o.receiveShadow = !String(o.userData.cadName).startsWith('lighting:');
      const interiorDetail = /:furniture:|:fixture_/.test(String(o.userData.cadName));
      const wall = /:wall_(?:external|partition)_|^roof:.*gable_wall$|:cladding:/.test(String(o.userData.cadName));
      if (wall) wallOutlines.set(o, null);
      else o.add(new LineSegments(new EdgesGeometry(o.geometry, 28), createOutlineMaterial(interiorDetail ? 0.16 : 0.55)));
    });
    updateWallOutlines();
  }
  function attachWallOutline(mesh: Mesh, geometry: BufferGeometry) {
    if (disposed || wallOutlines.get(mesh)) { geometry.dispose(); return; }
    const outline = new LineSegments(geometry, createOutlineMaterial());
    mesh.add(outline); wallOutlines.set(mesh, outline);
    renderer.domElement.dataset.wallOutlineCount = String([...wallOutlines.values()].filter(Boolean).length);
  }
  function updateWallOutlines() {
    const meshes = [...wallOutlines].filter(([mesh, outline]) => !outline && !pendingOutlines.has(mesh)).map(([mesh]) => mesh);
    if (!meshes.length) return;
    if (!useTypeScript && geometryWorker && !geometryWorker.failed) {
      if (!workerReady) return;
      const byId = new Map(meshes.map(mesh => [mesh.uuid, mesh]));
      const jobs = meshes.flatMap(mesh => {
        const geometryId = geometryWorker!.registerGeometry(mesh.geometry);
        if (disposed || geometryWorker!.failed) return [];
        if (!geometryId) { attachWallOutline(mesh, createCadOutlineGeometry(mesh.geometry, 28)); return []; }
        pendingOutlines.add(mesh);
        return [{ id: mesh.uuid, geometryId, thresholdAngle: 28 }];
      });
      if (disposed || geometryWorker.failed) return;
      void geometryWorker.outlines(jobs).then(results => {
        meshes.forEach(mesh => pendingOutlines.delete(mesh));
        if (disposed || !results) return;
        for (const result of results) {
          const mesh = byId.get(result.id);
          if (!mesh) continue;
          const geometry = new BufferGeometry();
          geometry.setAttribute('position', new BufferAttribute(result.positions, 3));
          attachWallOutline(mesh, geometry);
        }
        requestRender();
      });
      return;
    }
    for (const mesh of meshes) attachWallOutline(mesh, createCadOutlineGeometry(mesh.geometry, 28));
    requestRender();
  }
  function reportOverlay(status: StructuralOverlayState['status'], system: StructuralSystem | null) {
    const overlay = system ? overlays.get(system) : undefined;
    renderer.domElement.dataset.structureSystem = system ?? '';
    renderer.domElement.dataset.structureStatus = status;
    renderer.domElement.dataset.baseFoundationHidden = String(system !== null);
    renderer.domElement.dataset.structureMeshes = String(overlay ? visibleMeshes(overlay.root).length : 0);
    onOverlayState({ status, system, parts: overlay
      ? layout.parts.filter(part => overlay.objects.has(part.id)).map(part => part.id) : [] });
  }
  function activateOverlay() {
    cadObjects = new Map(baselineCadObjects);
    const overlay = structuralSystem ? overlays.get(structuralSystem) : undefined;
    if (overlay) for (const [name, object] of overlay.objects) cadObjects.set(name, object);
    // A newly loaded solid needs its section cap even if the cut height did not change.
    if (settings.cutaway) capHeight = null;
    apply(settings, null);
    // Recompute only the frustum: changing materials/city keeps orbit, pan and zoom.
    if (cameraInitialized) updateFrustum(); else fit();
  }
  function setStructure(system: StructuralSystem | null) {
    if (disposed || layout.id !== 'house') return;
    const changed = structuralSystem !== system;
    structuralSystem = system;
    if (changed) { clearHighlight(); selectedName = null; onSelection(null); }
    activateOverlay();
    if (system === null) { reportOverlay('idle', null); return; }
    if (overlays.has(system)) { reportOverlay('ready', system); return; }
    reportOverlay('loading', system);
    if (overlayLoads.has(system) || !root) return;
    const loading = new GLTFLoader().loadAsync(asset(`GLB/structure_${system}.glb`)).then(gltf => {
      if (disposed) { disposeObject(gltf.scene, true); return; }
      const objects = bindCadNodes(gltf);
      if (!objects.has('structure') || !objects.has('foundation')) {
        disposeObject(gltf.scene, true); throw new Error('Structural variant is missing its frame or foundation group.');
      }
      gltf.scene.visible = false;
      prepareMeshes(gltf.scene);
      // Exported variants use the exact original CAD origin. Parent to the already
      // centred architectural root so neither site bounds nor footing depth shift them.
      root!.add(gltf.scene); overlays.set(system, { root: gltf.scene, objects });
      if (structuralSystem === system) { activateOverlay(); reportOverlay('ready', system); }
    }).catch(() => {
      if (!disposed && structuralSystem === system) reportOverlay('error', system);
    }).finally(() => { overlayLoads.delete(system); });
    overlayLoads.set(system, loading);
  }
  const raycaster = new Raycaster();
  const activePointers = new Set<number>();
  let clickStart: { x: number; y: number; pointerId: number } | undefined;
  function pointerDown(event: PointerEvent) {
    activePointers.add(event.pointerId);
    clickStart = activePointers.size === 1 && event.button === 0
      ? { x: event.clientX, y: event.clientY, pointerId: event.pointerId } : undefined;
  }
  function pointerMove(event: PointerEvent) {
    if (clickStart && clickStart.pointerId === event.pointerId &&
      Math.hypot(event.clientX - clickStart.x, event.clientY - clickStart.y) > 5) clickStart = undefined;
  }
  function pointerUp(event: PointerEvent) {
    activePointers.delete(event.pointerId);
    const start = clickStart; clickStart = undefined;
    if (!root || !start || start.pointerId !== event.pointerId ||
      Math.hypot(event.clientX - start.x, event.clientY - start.y) > 5) return;
    const rect = renderer.domElement.getBoundingClientRect();
    raycaster.setFromCamera(new Vector2((event.clientX - rect.left) / rect.width * 2 - 1,
      -(event.clientY - rect.top) / rect.height * 2 + 1), camera);
    root.updateWorldMatrix(true, true);
    const hits = raycaster.intersectObjects(visibleMeshes(root), false);
    const hit = hits.find(item => renderer.clippingPlanes.every(plane => plane.distanceToPoint(item.point) >= 0));
    const selection = hit ? selectionFor(hit.object, layout) : null;
    select(selection?.name ?? null); onSelection(selection);
  }
  function pointerCancel(event: PointerEvent) { activePointers.delete(event.pointerId); clickStart = undefined; }
  function keyDown(event: KeyboardEvent) { if (event.key === 'Escape') { select(null); onSelection(null); } }
  renderer.domElement.addEventListener('pointerdown', pointerDown);
  renderer.domElement.addEventListener('pointermove', pointerMove);
  renderer.domElement.addEventListener('pointerup', pointerUp);
  renderer.domElement.addEventListener('pointercancel', pointerCancel);
  renderer.domElement.addEventListener('keydown', keyDown);
  function contextLost(event: Event) {
    event.preventDefault(); contextUnavailable = true; cancelAnimationFrame(frame); frame = 0; onError();
  }
  renderer.domElement.addEventListener('webglcontextlost', contextLost);
  renderer.domElement.addEventListener('webglcontextrestored', onContextRestored);
  if (!useTypeScript) {
    geometryWorker = createGeometryWorkerClient({ onFailure: () => {
      if (disposed) return;
      workerReady = false;
      renderer.domElement.dataset.sectionBackend = 'typescript-fallback';
      renderer.domElement.dataset.outlineBackend = 'typescript-fallback';
      pendingOutlines.clear(); updateWallOutlines();
      capHeight = null; apply(settings, selectedName);
    } });
    void geometryWorker.ready.then(() => {
      if (disposed) return;
      workerReady = true;
      renderer.domElement.dataset.sectionBackend = 'rust-wasm-worker';
      renderer.domElement.dataset.outlineBackend = 'rust-wasm-worker';
      updateWallOutlines();
      capHeight = null; apply(settings, selectedName);
    }).catch(() => { /* onFailure installs the TypeScript fallback. */ });
  }
  const modelUrl = new URL(asset(glbPath), location.href);
  const modelLoad = startModelLoad<GLTF>({
    url: modelUrl.href, onProgress,
    parse: bytes => new GLTFLoader().parseAsync(bytes, new URL('.', modelUrl).href),
    disposeLate: gltf => disposeObject(gltf.scene, true),
    onError: () => { if (!disposed) onError(); },
    onLoad: gltf => {
    if (disposed) { disposeObject(gltf.scene, true); return; }
    root = gltf.scene;
    cadObjects = bindCadNodes(gltf);
    baselineCadObjects = cadObjects;
    if (!centerModelAtFloorDatum(root, cadObjects)) {
      disposeObject(root, true); root = undefined; onError(); return;
    }
    prepareMeshes(root);
    for (const group of [...layout.groups, ...layout.parts]) {
      const object = cadObjects.get(group.id);
      if (!object) { disposeObject(root, true); root = undefined; onError(); return; }
      groupObjects.set(group.id, object);
    }
    scene.add(root); outdoorLighting.register(root); apply(settings); fit(); onReady();
    },
  });
  resize();
  return {
    captureCamera: () => root ? ({ mode, position: camera.position.toArray(), target: controls.target.toArray(), up: camera.up.toArray(), zoom: camera.zoom }) : null,
    restoreCamera(state) {
      mode = state.mode;
      camera.position.fromArray(state.position); controls.target.fromArray(state.target); camera.up.fromArray(state.up);
      camera.zoom = state.zoom; camera.updateProjectionMatrix(); controls.update(); requestRender();
    },
    apply,
    select,
    setTheme,
    setStructure,
    camera(next) { mode = next; fit(); },
    dispose() {
      disposed = true; modelLoad.cancel();
      renderer.domElement.removeEventListener('webglcontextlost', contextLost);
      renderer.domElement.removeEventListener('webglcontextrestored', onContextRestored);
      cancelAnimationFrame(frame); observer.disconnect(); controls.dispose();
      capGeneration++; geometryWorker?.dispose(); pendingOutlines.clear(); wallOutlines.clear();
      renderer.domElement.removeEventListener('pointerdown', pointerDown);
      renderer.domElement.removeEventListener('pointermove', pointerMove);
      renderer.domElement.removeEventListener('pointerup', pointerUp);
      renderer.domElement.removeEventListener('pointercancel', pointerCancel);
      renderer.domElement.removeEventListener('keydown', keyDown);
      clearHighlight();
      outdoorLighting.dispose();
      if (root) disposeObject(root, true);
      outlineMaterials.clear();
      environment.dispose();
      renderer.dispose(); renderer.domElement.remove();
    },
  };
}
