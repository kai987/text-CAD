import {
  Box3, Color, DirectionalLight, DoubleSide, EdgesGeometry, HemisphereLight, LineBasicMaterial,
  LineSegments, Mesh, Object3D, OrthographicCamera, Plane, Raycaster, Scene, Vector2, Vector3, WebGLRenderer,
} from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import type { Material, MeshStandardMaterial } from 'three';
import { asset } from './data';
import { groups, parts, settingsForPreset } from './model-state';
import type { ModelPartId, ModelSettings } from './model-state';
import { bindCadNodes, isObjectVisible, selectionFor, visibleMeshes } from './model-scene';
import type { ModelSelection } from './model-scene';

export interface HouseViewer {
  apply: (settings: ModelSettings, selectionName?: string | null) => void;
  camera: (mode: 'iso' | 'top') => void;
  select: (name: string | null) => void;
  dispose: () => void;
}

function disposeObject(root: Object3D) {
  const materials = new Set<Material>();
  root.traverse(o => {
    if (o instanceof Mesh || o instanceof LineSegments) {
      o.geometry.dispose();
      (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => materials.add(m));
    }
  });
  materials.forEach(m => m.dispose());
}

export function createHouseViewer(host: HTMLElement, onReady: () => void, onError: () => void,
  onSelection: (selection: ModelSelection | null) => void): HouseViewer {
  const renderer = new WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor('#f2f4f7');
  renderer.domElement.tabIndex = 0;
  renderer.domElement.setAttribute('aria-label', '可旋转和缩放的房屋三维模型');
  renderer.domElement.setAttribute('role', 'img');
  host.prepend(renderer.domElement);
  const scene = new Scene();
  scene.add(new HemisphereLight(0xffffff, 0xbac2cc, 2.2));
  const sun = new DirectionalLight(0xffffff, 2.2);
  sun.position.set(-8, 16, 12); scene.add(sun);
  const camera = new OrthographicCamera(-8, 8, 8, -8, 0.01, 500);
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
  let settings = settingsForPreset('exterior');
  const groupObjects = new Map<ModelPartId, Object3D>();
  let cadObjects = new Map<string, Object3D>();
  const originalMaterials = new Map<Mesh, Material | Material[]>();
  let selectedName: string | null = null;
  let halfHeight = 7;
  let mode: 'iso' | 'top' = 'iso';
  function draw() {
    frame = 0;
    if (disposed) return;
    controls.update(); renderer.render(scene, camera);
  }
  function requestRender() { if (!disposed && !frame) frame = requestAnimationFrame(draw); }
  controls.addEventListener('change', requestRender);
  function resize() {
    const width = host.clientWidth, height = host.clientHeight;
    if (!width || !height || disposed) return;
    renderer.setSize(width, height, false);
    camera.left = -halfHeight * width / height; camera.right = -camera.left;
    camera.top = halfHeight; camera.bottom = -halfHeight;
    camera.updateProjectionMatrix(); requestRender();
  }
  // Refit when the layout changes, so the full model remains visible on a narrow screen.
  const observer = new ResizeObserver(() => { if (root) fit(); else resize(); }); observer.observe(host);
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
    const aspect = Math.max(host.clientWidth / Math.max(host.clientHeight, 1), 0.1);
    halfHeight = Math.max((maxY - minY) / 2, (maxX - minX) / (2 * aspect)) * 1.3;
    controls.update(); resize();
  }
  function apply(next: ModelSettings, selectionName = selectedName) {
    settings = next;
    groups.forEach(g => { const part = groupObjects.get(g.id); if (part) part.visible = next.visibility[g.id]; });
    parts.forEach(p => { const part = groupObjects.get(p.id); if (part) part.visible = next.partVisibility[p.id]; });
    // GLB is Y-up/metres; display the cut height relative to the original F1 datum.
    renderer.clippingPlanes = next.cutaway ? [new Plane(new Vector3(0, -1, 0), next.heightMm / 1000 + floorOffset)] : [];
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
    const selection = hit ? selectionFor(hit.object) : null;
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
  new GLTFLoader().load(asset('GLB/house_3d.glb'), gltf => {
    if (disposed) { disposeObject(gltf.scene); return; }
    root = gltf.scene;
    cadObjects = bindCadNodes(gltf);
    const bounds = new Box3().setFromObject(root);
    const center = bounds.getCenter(new Vector3());
    floorOffset = -bounds.min.y;
    root.position.set(-center.x, floorOffset, -center.z);
    root.traverse(o => {
      if (!(o instanceof Mesh)) return;
      const materials = Array.isArray(o.material) ? o.material : [o.material];
      materials.forEach(m => { m.side = DoubleSide; m.polygonOffset = true; m.polygonOffsetFactor = 1; m.polygonOffsetUnits = 1; });
      const edges = new LineSegments(new EdgesGeometry(o.geometry, 28), new LineBasicMaterial({
        color: new Color('#535d68'), transparent: true, opacity: 0.55,
      }));
      o.add(edges);
    });
    for (const group of [...groups, ...parts]) {
      const object = cadObjects.get(group.id);
      if (!object) { disposeObject(root); root = undefined; onError(); return; }
      groupObjects.set(group.id, object);
    }
    scene.add(root); apply(settings); fit(); onReady();
  }, undefined, () => { if (!disposed) onError(); });
  resize();
  return {
    apply,
    select,
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
      if (root) disposeObject(root);
      renderer.dispose(); renderer.domElement.remove();
    },
  };
}
