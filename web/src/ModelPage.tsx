import { lazy, Suspense, useCallback, useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { RotateCcw, View } from 'lucide-react';
import { asset } from './data';
import type { ModelSettings } from './model-state';
import ModelControls from './ModelControls';

const ThreeScene = lazy(() => import('./ThreeScene'));
interface Props { settings: ModelSettings; setSettings: Dispatch<SetStateAction<ModelSettings>> }
export default function ModelPage({ settings, setSettings }: Props) {
  const [ready, setReady] = useState(false);
  const [cameraRequest, setCameraRequest] = useState({ mode: 'iso' as 'iso' | 'top', seq: 0 });
  const onReady = useCallback(() => setReady(true), []);
  const anyVisible = Object.values(settings.visibility).some(Boolean);
  return <div className="workspace model-workspace">
    <ModelControls settings={settings} setSettings={setSettings} ready={ready}
      onPreset={() => setCameraRequest(s => ({ mode: 'iso', seq: s.seq + 1 }))} />
    <section className="viewer-panel" aria-label="三维模型查看区域">
      <div className="viewer-toolbar">
        <h1>日本两层一户建</h1>
        <div className="toolbar-actions">
          <button type="button" className="outline-button" disabled={!ready} onClick={() =>
            setCameraRequest(s => ({ mode: 'top', seq: s.seq + 1 }))}><View size={16} aria-hidden="true" />俯视</button>
          <button type="button" className="outline-button" disabled={!ready} onClick={() =>
            setCameraRequest(s => ({ mode: 'iso', seq: s.seq + 1 }))}><RotateCcw size={16} aria-hidden="true" />重置视角</button>
        </div>
      </div>
      <div className="model-canvas">
        <Suspense fallback={<p className="canvas-message" role="status">正在加载查看器…</p>}>
          <ThreeScene settings={settings} cameraRequest={cameraRequest} onReady={onReady} />
        </Suspense>
        {ready && !anyVisible ? <p className="canvas-message" role="status">当前未显示部件，请勾选左侧部件。</p> : null}
        <div className="canvas-footer"><span>拖动旋转 · 滚轮缩放</span>
          <a href={asset('GLB/house_3d.glb')} download>下载 GLB</a></div>
      </div>
    </section>
  </div>;
}
