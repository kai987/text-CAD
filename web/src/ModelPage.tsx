import { lazy, Suspense, useCallback, useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { RotateCcw, View, X } from 'lucide-react';
import { asset } from './data';
import { useLanguage } from './LanguageContext';
import { selectionLabel } from './localization';
import type { ModelSettings } from './model-state';
import ModelControls from './ModelControls';
import ViewPresets from './ViewPresets';
import { anyVisible, groupVisibilityState, parts, setGroupVisible, setPartVisible } from './model-state';
import type { GroupId, ModelPartId, PartId } from './model-state';
import type { ModelSelection } from './model-scene';

const ThreeScene = lazy(() => import('./ThreeScene'));
interface Props { settings: ModelSettings; setSettings: Dispatch<SetStateAction<ModelSettings>> }
export default function ModelPage({ settings, setSettings }: Props) {
  const { copy } = useLanguage();
  const [ready, setReady] = useState(false);
  const [selection, setSelection] = useState<ModelSelection | null>(null);
  const [cameraRequest, setCameraRequest] = useState({ mode: 'iso' as 'iso' | 'top', seq: 0 });
  const onReady = useCallback((value: boolean) => { setReady(value); if (!value) setSelection(null); }, []);
  const hasVisible = anyVisible(settings);
  function selectPart(id: ModelPartId, fit = false) {
    const part = parts.find(p => p.id === id);
    setSettings(s => part ? setPartVisible(s, id as PartId, true)
      : groupVisibilityState(s, id as GroupId) === 'none' ? setGroupVisible(s, id as GroupId, true) : s);
    setSelection({ id, name: id, label: selectionLabel(copy, id) });
    if (fit) setCameraRequest(s => ({ mode: s.mode, seq: s.seq + 1 }));
  }
  return <div className="workspace model-workspace">
    <ModelControls settings={settings} setSettings={setSettings} ready={ready}
      selectedPart={selection?.id} onSelectPart={selectPart} />
    <section className="viewer-panel" aria-label={copy.model.region}>
      <div className="viewer-toolbar">
        <h1>{copy.model.title}</h1>
        <div className="toolbar-actions">
          <button type="button" className="outline-button" disabled={!ready} onClick={() =>
            setCameraRequest(s => ({ mode: 'top', seq: s.seq + 1 }))}><View size={16} aria-hidden="true" />{copy.model.top}</button>
          <button type="button" className="outline-button" disabled={!ready} onClick={() =>
            setCameraRequest(s => ({ mode: 'iso', seq: s.seq + 1 }))}><RotateCcw size={16} aria-hidden="true" />{copy.model.reset}</button>
        </div>
      </div>
      <ViewPresets settings={settings} setSettings={setSettings} ready={ready} onPreset={() => {
        setSelection(null); setCameraRequest(s => ({ mode: 'iso', seq: s.seq + 1 }));
      }} />
      <div className="model-canvas">
        <Suspense fallback={<p className="canvas-message" role="status">{copy.model.loadingViewer}</p>}>
          <ThreeScene settings={settings} cameraRequest={cameraRequest} onReady={onReady}
            selection={selection} onSelection={setSelection} />
        </Suspense>
        {ready && selection ? <div className="selection-details" role="status" aria-label={copy.model.selected}>
          <div><strong>{selectionLabel(copy, selection.id)}</strong><span>{selection.name}</span></div>
          <button type="button" className="selection-clear" aria-label={copy.model.clear} onClick={() => setSelection(null)}><X size={16} /></button>
        </div> : null}
        {ready && !hasVisible ? <p className="canvas-message" role="status">{copy.model.empty}</p> : null}
        <div className="canvas-footer"><span>{copy.model.gesture} <span className="desktop-gesture">{copy.model.wheel}</span><span className="mobile-gesture">{copy.model.touch}</span></span>
          <a href={asset('GLB/house_3d.glb')} download>{copy.model.downloadGlb}</a></div>
      </div>
    </section>
  </div>;
}
