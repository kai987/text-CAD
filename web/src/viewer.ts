import {
  Box3, Color, DirectionalLight, DoubleSide, EdgesGeometry, HemisphereLight, LineBasicMaterial,
  LineSegments, Mesh, Object3D, OrthographicCamera, Plane, Scene, Vector3, WebGLRenderer,
} from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import type { Material } from 'three';
import { asset } from './data';
import { groups, settingsForPreset } from './model-state';
import type { GroupId, ModelSettings } from './model-state';

export interface HouseViewer {
  apply: (settings: ModelSettings) => void;
  camera: (mode: 'iso' | 'top') => void;
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

export function createHouseViewer(host: HTMLElement, onReady: () => void, onError: () => void): HouseViewer {
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
  const groupObjects = new Map<GroupId, Object3D>();
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
  function isVisible(o: Object3D): boolean {
    for (let current: Object3D | null = o; current; current = current.parent) if (!current.visible) return false;
    return true;
  }
  function fit() {
    if (!root) return;
    root.updateWorldMatrix(true, true);
    const bounds = new Box3();
    root.traverse(o => { if (o instanceof Mesh && isVisible(o)) bounds.expandByObject(o); });
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
      if (!(o instanceof Mesh) || !isVisible(o)) return;
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
  function apply(next: ModelSettings) {
    settings = next;
    groups.forEach(g => { const part = groupObjects.get(g.id); if (part) part.visible = next.visibility[g.id]; });
    // GLB is Y-up/metres; display the cut height relative to the original F1 datum.
    renderer.clippingPlanes = next.cutaway ? [new Plane(new Vector3(0, -1, 0), next.heightMm / 1000 + floorOffset)] : [];
    requestRender();
  }
  function contextLost(event: Event) { event.preventDefault(); onError(); }
  renderer.domElement.addEventListener('webglcontextlost', contextLost);
  new GLTFLoader().load(asset('GLB/house_3d.glb'), gltf => {
    if (disposed) { disposeObject(gltf.scene); return; }
    root = gltf.scene;
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
    for (const group of groups) {
      const object = root.getObjectByName(group.id);
      if (!object) { disposeObject(root); root = undefined; onError(); return; }
      groupObjects.set(group.id, object);
    }
    scene.add(root); apply(settings); fit(); onReady();
  }, undefined, () => { if (!disposed) onError(); });
  resize();
  return {
    apply,
    camera(next) { mode = next; fit(); },
    dispose() {
      disposed = true; cancelAnimationFrame(frame); observer.disconnect(); controls.dispose();
      renderer.domElement.removeEventListener('webglcontextlost', contextLost);
      if (root) disposeObject(root);
      renderer.dispose(); renderer.domElement.remove();
    },
  };
}
