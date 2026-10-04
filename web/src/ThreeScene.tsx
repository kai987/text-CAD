import { useEffect, useRef, useState } from 'react';
import { createHouseViewer } from './viewer';
import type { HouseViewer } from './viewer';
import type { ModelSettings } from './model-state';
import { activePreset } from './model-state';
import { asset } from './data';

interface Props {
  settings: ModelSettings;
  cameraRequest: { mode: 'iso' | 'top'; seq: number };
  onReady: () => void;
}
export default function ThreeScene({ settings, cameraRequest, onReady }: Props) {
  const host = useRef<HTMLDivElement>(null);
  const viewer = useRef<HouseViewer | null>(null);
  const latest = useRef({ settings, cameraRequest });
  latest.current = { settings, cameraRequest };
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  useEffect(() => {
    let alive = true;
    try {
      const controller = createHouseViewer(host.current!, () => {
        if (!alive) return;
        controller.apply(latest.current.settings);
        controller.camera(latest.current.cameraRequest.mode);
        setStatus('ready'); onReady();
      }, () => { if (alive) setStatus('error'); });
      viewer.current = controller;
    } catch {
      setStatus('error');
    }
    return () => { alive = false; viewer.current?.dispose(); viewer.current = null; };
  }, [onReady]);
  useEffect(() => { viewer.current?.apply(settings); }, [settings]);
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
