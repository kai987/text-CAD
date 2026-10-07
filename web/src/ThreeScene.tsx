import { useEffect, useRef, useState } from 'react';
import { createHouseViewer } from './viewer';
import type { ViewerCameraState } from './viewer';
import type { ModelProgress } from './model-resource';
import type { HouseViewer } from './viewer';
import type { ModelSettings } from './model-state';
import { activePreset } from './model-state';
import { asset } from './data';
import type { ModelSelection } from './model-scene';
import { useModel } from './ModelContext';
import { useTheme } from './ThemeContext';
import type { StructuralOverlayState, StructuralSystem } from './structural-design';

interface Props {
  settings: ModelSettings;
  cameraRequest: { mode: 'iso' | 'top'; seq: number };
  onReady: (ready: boolean) => void;
  selection: ModelSelection | null;
  onSelection: (selection: ModelSelection | null) => void;
  structuralSystem: StructuralSystem | null;
  overlayAttempt: number;
  onOverlayState: (state: StructuralOverlayState) => void;
}
export default function ThreeScene({ settings, cameraRequest, onReady, selection, onSelection, structuralSystem, overlayAttempt, onOverlayState }: Props) {
  const { copy, layout, glb, fallback: modelFallback } = useModel();
  const { theme } = useTheme();
  const host = useRef<HTMLDivElement>(null);
  const viewer = useRef<HouseViewer | null>(null);
  const latest = useRef({ settings, cameraRequest, selection, theme, structuralSystem });
  latest.current = { settings, cameraRequest, selection, theme, structuralSystem };
  const savedCamera = useRef<ViewerCameraState | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [progress, setProgress] = useState<ModelProgress>({ loaded: 0, total: null });
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  useEffect(() => {
    let alive = true;
    setStatus('loading'); setProgress({ loaded: 0, total: null }); onReady(false);
    try {
      const controller = createHouseViewer(host.current!, () => {
        if (!alive) return;
        controller.apply(latest.current.settings, latest.current.selection?.name ?? null);
        controller.setStructure(latest.current.structuralSystem);
        if (savedCamera.current) controller.restoreCamera(savedCamera.current);
        else controller.camera(latest.current.cameraRequest.mode);
        setStatus('ready'); onReady(true);
      }, () => { if (alive) { savedCamera.current = viewer.current?.captureCamera() ?? null; setStatus('error'); onReady(false); } }, onSelection, latest.current.theme, layout, glb,
        state => { if (alive) onOverlayState(state); },
        value => { if (alive) setProgress(value); },
        () => { if (alive) setAttempt(value => value + 1); });
      viewer.current = controller;
    } catch {
      setStatus('error'); onReady(false);
    }
    return () => { alive = false; viewer.current?.dispose(); viewer.current = null; };
  }, [onReady, onSelection, onOverlayState, layout, glb, attempt]);
  useEffect(() => {
    host.current?.querySelector('canvas')?.setAttribute('aria-label', copy.model.canvas);
  }, [copy, status]);
  // Theme changes only recolor the canvas and outlines; the existing viewer stays mounted.
  useEffect(() => { viewer.current?.setTheme(theme); }, [theme, status]);
  // Visibility and selection must update together when isolation hides the previous selection.
  useEffect(() => { viewer.current?.apply(settings, selection?.name ?? null); }, [settings, selection]);
  useEffect(() => { viewer.current?.camera(cameraRequest.mode); }, [cameraRequest]);
  useEffect(() => { viewer.current?.setStructure(structuralSystem); }, [structuralSystem, overlayAttempt, status]);
  const preset = activePreset(settings, layout);
  const fallback = layout.id === 'house' && preset === 'first' ? 'output/review/house_3d_1f_interior.png'
    : layout.id === 'house' && preset === 'second' ? 'output/review/house_3d_2f_interior.png'
    : layout.id === 'house' && preset === 'structure' ? 'output/review/house_3d_structure.png'
    : layout.id === 'house' && preset === 'attic' ? 'output/review/house_3d_attic_interior.png' : modelFallback;
  return <div className="scene-host" ref={host}>
    {status === 'loading' ? <p className="canvas-message" role="status">{progress.loaded ? copy.model.loadingProgress.replace('{amount}', progress.total ? `${Math.min(100, Math.round(progress.loaded / progress.total * 100))}%` : `${(progress.loaded / 1_000_000).toFixed(1)} MB`) : copy.model.loadingModel}</p> : null}
    {status === 'error' ? <div className="viewer-fallback" role="alert">
      {structuralSystem === null ? <img src={asset(fallback)} alt={copy.model.fallback} /> : null}
      <p>{copy.model.error}</p>
      <button type="button" className="outline-button" onClick={() => setAttempt(value => value + 1)}>{copy.model.retry}</button>
    </div> : null}
  </div>;
}
