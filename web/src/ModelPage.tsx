import { lazy, Suspense, useCallback, useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { RotateCcw, View, X } from 'lucide-react';
import { asset } from './data';
import type { ModelSettings } from './model-state';
import ModelControls from './ModelControls';
import ViewPresets from './ViewPresets';
import { anyVisible, groups, groupVisibilityState, parts, setGroupVisible, setPartVisible } from './model-state';
import type { GroupId, ModelPartId, PartId } from './model-state';
import type { ModelSelection } from './model-scene';

const ThreeScene = lazy(() => import('./ThreeScene'));
interface Props { settings: ModelSettings; setSettings: Dispatch<SetStateAction<ModelSettings>> }
export default function ModelPage({ settings, setSettings }: Props) {
  const [ready, setReady] = useState(false);
  const [selection, setSelection] = useState<ModelSelection | null>(null);
  const [cameraRequest, setCameraRequest] = useState({ mode: 'iso' as 'iso' | 'top', seq: 0 });
  const onReady = useCallback((value: boolean) => { setReady(value); if (!value) setSelection(null); }, []);
  const hasVisible = anyVisible(settings);
  function selectPart(id: ModelPartId, fit = false) {
    const part = parts.find(p => p.id === id);
    setSettings(s => part ? setPartVisible(s, id as PartId, true)
      : groupVisibilityState(s, id as GroupId) === 'none' ? setGroupVisible(s, id as GroupId, true) : s);
    setSelection({ id, name: id, label: part ? `${groups.find(g => g.id === part.group)!.label} · ${part.label}`
      : groups.find(g => g.id === id)!.label });
    if (fit) setCameraRequest(s => ({ mode: s.mode, seq: s.seq + 1 }));
  }
  return <div className="workspace model-workspace">
    <ModelControls settings={settings} setSettings={setSettings} ready={ready}
      selectedPart={selection?.id} onSelectPart={selectPart} />
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
      <ViewPresets settings={settings} setSettings={setSettings} ready={ready} onPreset={() => {
        setSelection(null); setCameraRequest(s => ({ mode: 'iso', seq: s.seq + 1 }));
      }} />
      <div className="model-canvas">
        <Suspense fallback={<p className="canvas-message" role="status">正在加载查看器…</p>}>
          <ThreeScene settings={settings} cameraRequest={cameraRequest} onReady={onReady}
            selection={selection} onSelection={setSelection} />
        </Suspense>
        {ready && selection ? <div className="selection-details" role="status" aria-label="已选部件">
          <div><strong>{selection.label}</strong><span>{selection.name}</span></div>
          <button type="button" className="selection-clear" aria-label="清除部件高亮" onClick={() => setSelection(null)}><X size={16} /></button>
        </div> : null}
        {ready && !hasVisible ? <p className="canvas-message" role="status">当前未显示部件，请勾选需要查看的部件。</p> : null}
        <div className="canvas-footer"><span>点选部件 · 拖动旋转 · <span className="desktop-gesture">滚轮</span><span className="mobile-gesture">双指</span>缩放</span>
          <a href={asset('GLB/house_3d.glb')} download>下载 GLB</a></div>
      </div>
    </section>
  </div>;
}
