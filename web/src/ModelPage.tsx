import { lazy, Suspense, useCallback, useEffect, useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { RotateCcw, View, X } from 'lucide-react';
import { asset } from './data';
import { useModel } from './ModelContext';
import { useLanguage } from './LanguageContext';
import { cadComponentLabel } from './cad-component-labels';
import { selectionLabel } from './localization';
import type { ModelSettings } from './model-state';
import ModelControls from './ModelControls';
import FurnitureToggle from './FurnitureToggle';
import SceneLightingControls from './SceneLightingControls';
import ViewPresets from './ViewPresets';
import { anyVisible, groupVisibilityState, initialPreset, setGroupVisible, setPartVisible } from './model-state';
import type { GroupId, ModelPartId, PartId } from './model-state';
import type { ModelSelection } from './model-scene';
import StructuralOptions from './StructuralOptions';
import { useStructuralDesign } from './StructuralDesignContext';
import { structuralCopy, structuralDesignUrl, structuralPaths } from './structural-design';
import type { StructuralOverlayState } from './structural-design';

const ThreeScene = lazy(() => import('./ThreeScene'));
interface Props { settings: ModelSettings; setSettings: Dispatch<SetStateAction<ModelSettings>> }
export default function ModelPage({ settings, setSettings }: Props) {
  const { copy, layout, glb } = useModel();
  const { locale } = useLanguage();
  const { design } = useStructuralDesign();
  const [ready, setReady] = useState(false);
  const [structuralMode, setStructuralMode] = useState(() => layout.id === 'house' && initialPreset(location.search, layout) === 'structure');
  const [overlayState, setOverlayState] = useState<StructuralOverlayState>({ status: 'idle', system: null, parts: [] });
  const [overlayAttempt, setOverlayAttempt] = useState(0);
  const [selection, setSelection] = useState<ModelSelection | null>(null);
  const [cameraRequest, setCameraRequest] = useState({ mode: 'iso' as 'iso' | 'top', seq: 0 });
  const onReady = useCallback((value: boolean) => { setReady(value); if (!value) setSelection(null); }, []);
  useEffect(() => {
    if (layout.id === 'house') history.replaceState(null, '', structuralDesignUrl(location.href, design));
  }, [layout.id, design]);
  const structuralParts = structuralMode && overlayState.status === 'ready' ? overlayState.parts : undefined;
  const displayLayout = structuralParts ? { ...layout, parts: layout.parts.filter(part =>
    !['structure', 'foundation'].includes(part.group) || structuralParts.includes(part.id)) } : layout;
  const hasVisible = anyVisible(settings, displayLayout);
  const componentName = selection ? cadComponentLabel(locale, selection.name, layout.id) : null;
  function selectPart(id: ModelPartId, fit = false) {
    const part = layout.parts.find(p => p.id === id);
    setSettings(s => part ? setPartVisible(s, id as PartId, true, layout)
      : groupVisibilityState(s, id as GroupId, layout) === 'none' ? setGroupVisible(s, id as GroupId, true, layout) : s);
    setSelection({ id, name: id, label: selectionLabel(copy, id) });
    if (fit) setCameraRequest(s => ({ mode: s.mode, seq: s.seq + 1 }));
  }
  return <div className="workspace model-workspace">
    <ModelControls settings={settings} setSettings={setSettings} ready={ready}
      selectedPart={selection?.id} onSelectPart={selectPart}
      structuralParts={structuralParts} />
    <section className="viewer-panel" aria-label={copy.model.region}>
      <div className="viewer-toolbar">
        <h1>{copy.model.title}</h1>
        <div className="toolbar-actions">
          <FurnitureToggle settings={settings} setSettings={setSettings} ready={ready} />
          <button type="button" className="outline-button" disabled={!ready} onClick={() =>
            setCameraRequest(s => ({ mode: 'top', seq: s.seq + 1 }))}><View size={16} aria-hidden="true" />{copy.model.top}</button>
          <button type="button" className="outline-button" disabled={!ready} onClick={() =>
            setCameraRequest(s => ({ mode: 'iso', seq: s.seq + 1 }))}><RotateCcw size={16} aria-hidden="true" />{copy.model.reset}</button>
        </div>
      </div>
      <SceneLightingControls settings={settings} setSettings={setSettings} ready={ready} />
      {layout.id === 'house' ? <StructuralOptions compact showSummary={structuralMode} /> : null}
      <ViewPresets settings={settings} setSettings={setSettings} ready={ready} structuralMode={structuralMode} onPreset={preset => {
        setStructuralMode(preset === 'structure');
        const url = new URL(location.href); url.searchParams.set('mode', preset);
        history.replaceState(null, '', url.href);
        setSelection(null); setCameraRequest(s => ({ mode: 'iso', seq: s.seq + 1 }));
      }} />
      <div className="model-canvas" data-scene-environment={settings.environment}>
        <Suspense fallback={<p className="canvas-message" role="status">{copy.model.loadingViewer}</p>}>
          <ThreeScene settings={settings} cameraRequest={cameraRequest} onReady={onReady}
            selection={selection} onSelection={setSelection}
            structuralSystem={structuralMode ? design.system : null} overlayAttempt={overlayAttempt} onOverlayState={setOverlayState} />
        </Suspense>
        {structuralMode && ['loading', 'error'].includes(overlayState.status) ? <div className="structural-load-status" role={overlayState.status === 'error' ? 'alert' : 'status'}>
          <p>{overlayState.status === 'error' ? structuralCopy.loadError[locale] : structuralCopy.loading[locale]}</p>
          {overlayState.status === 'error' ? <button type="button" className="outline-button" onClick={() => setOverlayAttempt(value => value + 1)}>{structuralCopy.retry[locale]}</button> : null}
        </div> : null}
        {ready && selection ? <div className="selection-details" role="status" aria-label={copy.model.selected}>
          <div><strong>{selectionLabel(copy, selection.id)}</strong>{componentName ? <span>{componentName}</span> : null}</div>
          <button type="button" className="selection-clear" aria-label={copy.model.clear} onClick={() => setSelection(null)}><X size={16} /></button>
        </div> : null}
        {ready && !hasVisible ? <p className="canvas-message" role="status">{copy.model.empty}</p> : null}
        <div className="canvas-footer"><span>{copy.model.gesture} <span className="desktop-gesture">{copy.model.wheel}</span><span className="mobile-gesture">{copy.model.touch}</span></span>
          <a href={asset(structuralMode ? structuralPaths(design).glb : glb)} download>{copy.model.downloadGlb}</a></div>
      </div>
    </section>
  </div>;
}
