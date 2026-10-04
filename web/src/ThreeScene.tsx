import { useEffect, useRef, useState } from 'react';
import { createHouseViewer } from './viewer';
import type { HouseViewer } from './viewer';
import type { ModelSettings } from './model-state';
import { activePreset } from './model-state';
import { asset } from './data';
import type { ModelSelection } from './model-scene';

interface Props {
  settings: ModelSettings;
  cameraRequest: { mode: 'iso' | 'top'; seq: number };
  onReady: (ready: boolean) => void;
  selection: ModelSelection | null;
  onSelection: (selection: ModelSelection | null) => void;
}
export default function ThreeScene({ settings, cameraRequest, onReady, selection, onSelection }: Props) {
  const host = useRef<HTMLDivElement>(null);
  const viewer = useRef<HouseViewer | null>(null);
  const latest = useRef({ settings, cameraRequest, selection });
  latest.current = { settings, cameraRequest, selection };
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  useEffect(() => {
    let alive = true;
    try {
      const controller = createHouseViewer(host.current!, () => {
        if (!alive) return;
        controller.apply(latest.current.settings, latest.current.selection?.name ?? null);
        controller.camera(latest.current.cameraRequest.mode);
        setStatus('ready'); onReady(true);
      }, () => { if (alive) { setStatus('error'); onReady(false); } }, onSelection);
      viewer.current = controller;
    } catch {
      setStatus('error'); onReady(false);
    }
    return () => { alive = false; viewer.current?.dispose(); viewer.current = null; };
  }, [onReady, onSelection]);
  // Visibility and selection must update together when isolation hides the previous selection.
  useEffect(() => { viewer.current?.apply(settings, selection?.name ?? null); }, [settings, selection]);
  useEffect(() => { viewer.current?.camera(cameraRequest.mode); }, [cameraRequest]);
  const preset = activePreset(settings);
  const fallback = preset === 'first' ? 'house_3d_1f_interior.png' : preset === 'second' ? 'house_3d_2f_interior.png' : 'house_3d_iso.png';
  return <div className="scene-host" ref={host}>
    {status === 'loading' ? <p className="canvas-message" role="status">正在加载房屋模型…</p> : null}
    {status === 'error' ? <div className="viewer-fallback" role="alert">
      <img src={asset(`output/review/${fallback}`)} alt="房屋模型静态预览" />
      <p>当前浏览器无法显示交互模型。你仍可查看平面图或下载 GLB、STEP 文件。</p>
    </div> : null}
  </div>;
}
