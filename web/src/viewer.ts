import {
  Box3, Color, DirectionalLight, DoubleSide, EdgesGeometry, FrontSide, HemisphereLight, LineBasicMaterial,
  LineSegments, Mesh, Object3D, OrthographicCamera, Plane, PMREMGenerator, Raycaster, Scene, Texture, Vector2, Vector3, WebGLRenderer,
} from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import type { Material, MeshStandardMaterial } from 'three';
import { asset } from './data';
import { modelLayouts, settingsForPreset } from './model-state';
import type { ModelLayout, ModelPartId, ModelSettings } from './model-state';
import { bindCadNodes, isObjectVisible, selectionFor, visibleMeshes } from './model-scene';
import type { ModelSelection } from './model-scene';
import { createHorizontalCap, createSectionMaterial } from './section-caps';
import { createCadOutlineGeometry } from './cad-outlines';
import { themePalette } from './theme-preferences';
import type { ResolvedTheme } from './theme-preferences';

export interface HouseViewer {
  apply: (settings: ModelSettings, selectionName?: string | null) => void;
  camera: (mode: 'iso' | 'top') => void;
  select: (name: string | null) => void;
  setTheme: (theme: ResolvedTheme) => void;
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
  layout: ModelLayout = modelLayouts.house, glbPath = 'GLB/house_3d.glb'): HouseViewer {
  let theme = initialTheme;
  const outlineMaterials = new Set<LineBasicMaterial>();
  function createOutlineMaterial(opacity = 0.55) {
    const material = new LineBasicMaterial({
      color: new Color(themePalette[theme].outline), transparent: true, opacity,
    });
    outlineMaterials.add(material);
    return material;
  }
  const renderer = new WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(themePalette[theme].canvasBackground);
  renderer.domElement.tabIndex = 0;
  renderer.domElement.setAttribute('aria-label', '可旋转和缩放的房屋三维模型');
  renderer.domElement.setAttribute('role', 'img');
  renderer.domElement.dataset.sectionBackend = 'typescript';
  host.prepend(renderer.domElement);
  const scene = new Scene();
  // Local studio lighting gives ceramic, glass and metal highlights without a remote HDR asset.
  const studio = new RoomEnvironment();
  const pmrem = new PMREMGenerator(renderer);
  const environment = pmrem.fromScene(studio, 0.04);
  scene.environment = environment.texture;
  scene.environmentIntensity = 0.12;
  studio.dispose(); pmrem.dispose();
  scene.add(new HemisphereLight(0xffffff, 0xbac2cc, 1.8));
  const sun = new DirectionalLight(0xffffff, 2.0);
  sun.position.set(-8, 16, 12); scene.add(sun);
  const camera = new OrthographicCamera(-8, 8, 8, -8, 0.1, 100);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.12;
  controls.minZoom = 0.15; controls.maxZoom = 12;
  controls.maxPolarAngle = Math.PI * 0.94;
  controls.listenToKeyEvents(renderer.domElement);
  let disposed = false;
  let frame = 0;
  let root: Object3D | undefined;
  let floorOffset = 0;
  let settings = settingsForPreset(layout.defaultPreset, layout);
  const groupObjects = new Map<ModelPartId, Object3D>();
  let cadObjects = new Map<string, Object3D>();
  const originalMaterials = new Map<Mesh, Material | Material[]>();
  const sourceMeshes: Mesh[] = [];
  const sectionCaps = new Map<Mesh, Mesh>();
  let capHeight: number | null = null;
  let createCap = createHorizontalCap;
  let selectedName: string | null = null;
  let halfHeight = 7;
  let mode: 'iso' | 'top' = 'iso';
  function draw() {
    frame = 0;
    if (disposed || !host.clientWidth || !host.clientHeight) return;
    controls.update(); renderer.render(scene, camera);
  }
  function requestRender() { if (!disposed && !frame) frame = requestAnimationFrame(draw); }
  function setTheme(next: ResolvedTheme) {
    if (disposed) return;
    theme = next;
    renderer.setClearColor(themePalette[theme].canvasBackground);
    outlineMaterials.forEach(material => material.color.set(themePalette[theme].outline));
    requestRender();
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
  function updateSectionCaps(height: number | null) {
    if (!root || height === capHeight) return;
    capHeight = height;
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
    if (height === null) return;
    root.updateWorldMatrix(true, true);
    for (const mesh of sourceMeshes) {
      const material = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
      if (material.transparent || material.opacity < 1) continue;
      // Place the display-only cap 0.05 mm below the plane to avoid GPU clip round-off.
      const geometry = createCap(mesh, height - 0.00005);
      if (!geometry) continue;
      const cap = new Mesh(geometry, createSectionMaterial(material));
      cap.name = `${mesh.name}_section_cap`;
      cap.userData.cadName = mesh.userData.cadName;
      cap.userData.sectionCap = true;
      cap.add(new LineSegments(new EdgesGeometry(geometry, 28), createOutlineMaterial()));
      mesh.add(cap); sectionCaps.set(mesh, cap);
    }
  }
  function fit() {
    if (!root) return;
    root.updateWorldMatrix(true, true);
    const bounds = new Box3();
    root.traverse(o => { if (o instanceof Mesh && isObjectVisible(o)) bounds.expandByObject(o); });
    if (bounds.isEmpty()) return;
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
    // GLB is Y-up/metres; display the cut height relative to the original F1 datum.
    const height = next.cutaway ? next.heightMm / 1000 + floorOffset : null;
    renderer.clippingPlanes = height === null ? [] : [new Plane(new Vector3(0, -1, 0), height)];
    updateSectionCaps(height);
    if (selectionName) {
      const target = cadObjects.get(selectionName);
      if (!target || !visibleMeshes(target).length) { select(null); onSelection(null); }
      else select(selectionName);
    } else select(null);
    requestRender();
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
  function contextLost(event: Event) { event.preventDefault(); onError(); }
  renderer.domElement.addEventListener('webglcontextlost', contextLost);
  new GLTFLoader().load(asset(glbPath), gltf => {
    if (disposed) { disposeObject(gltf.scene, true); return; }
    root = gltf.scene;
    cadObjects = bindCadNodes(gltf);
    const bounds = new Box3().setFromObject(root);
    const center = bounds.getCenter(new Vector3());
    floorOffset = -bounds.min.y;
    root.position.set(-center.x, floorOffset, -center.z);
    root.traverse(o => {
      if (!(o instanceof Mesh)) return;
      sourceMeshes.push(o);
      const materials = Array.isArray(o.material) ? o.material : [o.material];
      materials.forEach(m => {
        // Closed solids need outward faces only: cabinet backs touch walls with opposite normals.
        m.side = m.transparent ? DoubleSide : FrontSide;
        // Pull outline lines forward through a fill offset; back-face culling prevents shared-face fighting.
        m.polygonOffset = true; m.polygonOffsetFactor = 1; m.polygonOffsetUnits = 1;
      });
      const interiorDetail = /:furniture:|:fixture_/.test(String(o.userData.cadName));
      const wall = /:wall_(?:external|partition)_|^roof:.*gable_wall$|:cladding:/.test(String(o.userData.cadName));
      // Architectural CAD faces may have collinear triangle edges with different endpoints.
      const outline = wall ? createCadOutlineGeometry(o.geometry, 28) : new EdgesGeometry(o.geometry, 28);
      const edges = new LineSegments(outline, createOutlineMaterial(interiorDetail ? 0.16 : 0.55));
      o.add(edges);
    });
    for (const group of [...layout.groups, ...layout.parts]) {
      const object = cadObjects.get(group.id);
      if (!object) { disposeObject(root, true); root = undefined; onError(); return; }
      groupObjects.set(group.id, object);
    }
    scene.add(root); apply(settings); fit(); onReady();
  }, undefined, () => { if (!disposed) onError(); });
  // Opt-in prototype: keep the model usable while the optional engine initializes.
  if (new URLSearchParams(location.search).get('section') === 'wasm') {
    renderer.domElement.dataset.sectionBackend = 'loading-wasm';
    void import('./section-caps-wasm').then(async module => {
      await module.initializeSectionCapsWasm();
      if (disposed) return;
      createCap = module.createWasmHorizontalCap;
      renderer.domElement.dataset.sectionBackend = 'rust-wasm';
      // Rebuild an already visible section without resetting camera or selection.
      capHeight = null;
      apply(settings, selectedName);
    }).catch(() => {
      if (disposed) return;
      createCap = createHorizontalCap;
      renderer.domElement.dataset.sectionBackend = 'typescript-fallback';
      capHeight = null;
      apply(settings, selectedName);
    });
  }
  resize();
  return {
    apply,
    select,
    setTheme,
    camera(next) { mode = next; fit(); },
    dispose() {
      disposed = true; cancelAnimationFrame(frame); observer.disconnect(); controls.dispose();
      renderer.domElement.removeEventListener('webglcontextlost', contextLost);
      renderer.domElement.removeEventListener('pointerdown', pointerDown);
      renderer.domElement.removeEventListener('pointermove', pointerMove);
      renderer.domElement.removeEventListener('pointerup', pointerUp);
      renderer.domElement.removeEventListener('pointercancel', pointerCancel);
      renderer.domElement.removeEventListener('keydown', keyDown);
      clearHighlight();
      if (root) disposeObject(root, true);
      outlineMaterials.clear();
      environment.dispose();
      renderer.dispose(); renderer.domElement.remove();
    },
  };
}
