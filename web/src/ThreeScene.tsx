import { useEffect, useRef, useState } from 'react';
import { createHouseViewer } from './viewer';
import type { HouseViewer } from './viewer';
import type { ModelSettings } from './model-state';
import { activePreset } from './model-state';
import { asset } from './data';
import type { ModelSelection } from './model-scene';
import { useModel } from './ModelContext';
import { useTheme } from './ThemeContext';

interface Props {
  settings: ModelSettings;
  cameraRequest: { mode: 'iso' | 'top'; seq: number };
  onReady: (ready: boolean) => void;
  selection: ModelSelection | null;
  onSelection: (selection: ModelSelection | null) => void;
}
export default function ThreeScene({ settings, cameraRequest, onReady, selection, onSelection }: Props) {
  const { copy, layout, glb, fallback: modelFallback } = useModel();
  const { theme } = useTheme();
  const host = useRef<HTMLDivElement>(null);
  const viewer = useRef<HouseViewer | null>(null);
  const latest = useRef({ settings, cameraRequest, selection, theme });
  latest.current = { settings, cameraRequest, selection, theme };
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  useEffect(() => {
    let alive = true;
    try {
      const controller = createHouseViewer(host.current!, () => {
        if (!alive) return;
        controller.apply(latest.current.settings, latest.current.selection?.name ?? null);
        controller.camera(latest.current.cameraRequest.mode);
        setStatus('ready'); onReady(true);
      }, () => { if (alive) { setStatus('error'); onReady(false); } }, onSelection, latest.current.theme, layout, glb);
      viewer.current = controller;
    } catch {
      setStatus('error'); onReady(false);
    }
    return () => { alive = false; viewer.current?.dispose(); viewer.current = null; };
  }, [onReady, onSelection, layout, glb]);
  useEffect(() => {
    host.current?.querySelector('canvas')?.setAttribute('aria-label', copy.model.canvas);
  }, [copy, status]);
  // Theme changes only recolor the canvas and outlines; the existing viewer stays mounted.
  useEffect(() => { viewer.current?.setTheme(theme); }, [theme, status]);
  // Visibility and selection must update together when isolation hides the previous selection.
  useEffect(() => { viewer.current?.apply(settings, selection?.name ?? null); }, [settings, selection]);
  useEffect(() => { viewer.current?.camera(cameraRequest.mode); }, [cameraRequest]);
  const preset = activePreset(settings, layout);
  const fallback = layout.id === 'house' && preset === 'first' ? 'output/review/house_3d_1f_interior.png'
    : layout.id === 'house' && preset === 'second' ? 'output/review/house_3d_2f_interior.png' : modelFallback;
  return <div className="scene-host" ref={host}>
    {status === 'loading' ? <p className="canvas-message" role="status">{copy.model.loadingModel}</p> : null}
    {status === 'error' ? <div className="viewer-fallback" role="alert">
      <img src={asset(fallback)} alt={copy.model.fallback} />
      <p>{copy.model.error}</p>
    </div> : null}
  </div>;
}
