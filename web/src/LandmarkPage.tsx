import { useEffect, useRef, useState } from 'react';
import { X } from 'lucide-react';
import { asset, repository } from './data';
import { useLanguage } from './LanguageContext';
import { useTheme } from './ThemeContext';
import { isLocale, languageNames, locales } from './localization';
import { isThemePreference } from './theme-preferences';
import { initialSceneLighting, saveSceneLighting, sceneLightingUrl } from './scene-lighting-settings';
import { riverCopy, residentialUrl, riverUrl } from './river-copy';
import { initialLandmarkView, isLandmarkId, landmarkCameraOptions, landmarkCopy, landmarkDownloadFiles, landmarkGroupIds, landmarkIds, landmarkModels, landmarkUrl, landmarkViews } from './landmark-copy';
import type { LandmarkCamera, LandmarkGroupId, LandmarkId, LandmarkView } from './landmark-copy';
import type { LandmarkViewer } from './landmark-viewer';
import type { LandmarkSteelNode, SteelMicroMode } from './landmark-steel-nodes';
import type { ModelProgress } from './model-resource';
import { loadFailureMessage } from './model-load-error';
import { formatDownloadBytes } from './download-copy';
import { loadDownloadManifest } from './download-resource';
import type { ArtifactManifest } from './download-resource';
import DownloadFile from './DownloadFile';
import ReferenceCompare from './ReferenceCompare';
import './landmarks.css';

const allVisible = () => Object.fromEntries(landmarkGroupIds.map(id => [id, true])) as Record<LandmarkGroupId, boolean>;
function LandmarkDrawing({ model, kind, active }: { model: LandmarkId; kind: 'plan' | 'elevation'; active: boolean }) {
  const { locale } = useLanguage(); const copy = landmarkCopy[locale];
  const [phase, setPhase] = useState<'loading' | 'ready' | 'error'>('loading');
  const [attempt, setAttempt] = useState(0); const [zoom, setZoom] = useState(1);
  const url = asset(`output/svg/${landmarkModels[model].stem}_${kind}.svg`);
  const source = attempt ? `${url}${url.includes('?') ? '&' : '?'}retry=${attempt}` : url;
  return <section className="landmark-drawing" hidden={!active} aria-label={copy.tabs[kind]}>
    <div className="viewer-toolbar"><h1>{landmarkModels[model].names[locale]} · {copy.tabs[kind]}</h1>
      <div className="toolbar-actions" aria-label={copy.zoom}>
        <button className="outline-button" aria-label={`${copy.zoom} −`} disabled={zoom <= 1} onClick={() => setZoom(value => Math.max(1, value - .25))}>−</button>
        <span className="landmark-zoom">{Math.round(zoom * 100)}%</span>
        <button className="outline-button" aria-label={`${copy.zoom} +`} disabled={zoom >= 3} onClick={() => setZoom(value => Math.min(3, value + .25))}>+</button>
        <button className="outline-button" onClick={() => setZoom(1)}>{copy.reset}</button>
      </div>
    </div>
    <p className="landmark-drawing-note">{copy.drawingNote}</p>
    <div className="landmark-paper-scroll" aria-busy={phase === 'loading'}>
      <img key={attempt} src={source} alt={`${landmarkModels[model].names[locale]} · ${copy.tabs[kind]}`} className="landmark-paper" style={{ width: `${zoom * 100}%` }}
        onLoad={() => setPhase('ready')} onError={() => setPhase('error')} />
      {phase === 'loading' ? <p className="landmark-drawing-status" role="status">{copy.planLoading}</p> : null}
      {phase === 'error' ? <div className="landmark-drawing-status" role="alert"><p>{copy.planError}</p>
        <button className="outline-button" onClick={() => { setPhase('loading'); setAttempt(value => value + 1); }}>{copy.retry}</button></div> : null}
    </div>
  </section>;
}

export default function LandmarkPage({ model }: { model: LandmarkId }) {
  const { locale, setLocale, copy: base } = useLanguage(); const { preference, setPreference, theme } = useTheme();
  const copy = landmarkCopy[locale]; const metadata = landmarkModels[model]; const name = metadata.names[locale];
  const [page, setPage] = useState<LandmarkView>(() => initialLandmarkView(location.search));
  const [visibility, setVisibility] = useState(allVisible);
  const [selection, setSelection] = useState<LandmarkGroupId | null>(null);
  const [camera, setCamera] = useState<LandmarkCamera>('iso');
  const [steelNodes, setSteelNodes] = useState<readonly LandmarkSteelNode[]>([]);
  const [steelNode, setSteelNode] = useState('');
  const [steelMicro, setSteelMicro] = useState<SteelMicroMode>('auto');
  const [lighting, setLighting] = useState(() => {
    try { return initialSceneLighting(location.search, window.localStorage); } catch { return initialSceneLighting(location.search); }
  });
  const [phase, setPhase] = useState<'loading' | 'ready' | 'error'>('loading');
  const [modelError, setModelError] = useState<unknown>(null);
  const [progress, setProgress] = useState<ModelProgress | null>(null); const [attempt, setAttempt] = useState(0);
  const [manifest, setManifest] = useState<ArtifactManifest | null>(null);
  const host = useRef<HTMLDivElement | null>(null); const viewer = useRef<LandmarkViewer | null>(null);
  const live = useRef({ theme, name, visibility, night: lighting.environment === 'night', steelMicro });
  live.current = { theme, name, visibility, night: lighting.environment === 'night', steelMicro };
  useEffect(() => {
    document.title = `${name} · text-CAD`;
    document.querySelector('meta[name="description"]')?.setAttribute('content', copy.description);
  }, [name, copy.description]);
  useEffect(() => {
    try { saveSceneLighting(window.localStorage, lighting); } catch { /* Embedded storage can be blocked. */ }
    history.replaceState(null, '', sceneLightingUrl(location.href, lighting));
  }, [lighting]);
  useEffect(() => {
    let active = true; setPhase('loading'); setProgress(null); setModelError(null); setSteelNodes([]);
    void import('./landmark-viewer').then(({ createLandmarkViewer }) => {
      if (!active || !host.current) return;
      const current = live.current;
      const instance = createLandmarkViewer(host.current, model, {
        opaqueBatching: new URLSearchParams(location.search).get('renderBatching') !== 'off',
        theme: current.theme, night: current.night, label: current.name,
        onReady: () => { if (active) setPhase('ready'); }, onError: error => { if (active) { setModelError(error); setPhase('error'); } },
        onProgress: value => { if (active) setProgress(value); }, onSelection: value => { if (active) setSelection(value); },
        onSteelNodes: value => { if (active) { setSteelNodes(value); setSteelNode(previous => value.some(node => node.id === previous) ? previous : value[0]?.id ?? ''); } },
        onSteelNodeSelection: value => { if (active) setSteelNode(value); },
      });
      viewer.current = instance; instance.visibility(current.visibility); instance.steelMicro(current.steelMicro);
    }).catch(() => { if (active) setPhase('error'); });
    return () => { active = false; viewer.current?.dispose(); viewer.current = null; };
  }, [model, attempt]);
  useEffect(() => { viewer.current?.visibility(visibility); }, [visibility]);
  useEffect(() => { viewer.current?.appearance(theme, lighting.environment === 'night'); viewer.current?.label(name); }, [theme, lighting.environment, name]);
  useEffect(() => {
    let active = true;
    void loadDownloadManifest(asset('manifest.json')).then(value => { if (active) setManifest(value); });
    return () => { active = false; };
  }, []);
  function navigate(next: LandmarkView) { setPage(next); history.replaceState(null, '', landmarkUrl(location.href, model, next)); }
  function changeModel(id: string) {
    if (isLandmarkId(id)) location.assign(landmarkUrl(location.href, id, '3d'));
    else if (id === 'river') location.assign(riverUrl(location.href, '3d'));
    else if (id === 'house' || id === 'apartment') location.assign(residentialUrl(location.href, id));
  }
  const ready = phase === 'ready';
  const metres = (value: number) => `${new Intl.NumberFormat(locale, { maximumFractionDigits: 2 }).format(value / 1000)} m`;
  return <div className="app-shell landmark-app">
    <a className="skip-link" href="#main-content">{base.app.skip}</a>
    <header className="app-header">
      <a className="wordmark" href={import.meta.env.BASE_URL} aria-label={base.app.home}>text-CAD</a>
      <nav aria-label={copy.nav}>{landmarkViews.map(id => <button key={id} className={page === id ? 'nav-tab active' : 'nav-tab'}
        aria-current={page === id ? 'page' : undefined} onClick={() => navigate(id)}>{copy.tabs[id]}</button>)}</nav>
      <div className="header-actions">
        <label className="theme-control"><span className="sr-only">{base.theme.label}</span><select value={preference} title={base.theme.help}
          onChange={event => { if (isThemePreference(event.target.value)) setPreference(event.target.value); }}>
          <option value="system">{base.theme.system}</option><option value="light">{base.theme.light}</option><option value="dark">{base.theme.dark}</option>
        </select></label>
        <label className="language-control"><span className="sr-only">{base.app.language}</span><select value={locale}
          onChange={event => { if (isLocale(event.target.value)) setLocale(event.target.value); }}>
          {locales.map(id => <option key={id} value={id} lang={id === 'zh' ? 'zh-CN' : id}>{languageNames[id]}</option>)}
        </select></label>
        <a className="repo-link" href={repository} target="_blank" rel="noreferrer">GitHub</a>
      </div>
    </header>
    <div className="model-switcher"><label htmlFor="model-choice">{copy.modelLabel}</label>
      <select id="model-choice" value={model} onChange={event => changeModel(event.target.value)}>
        <option value="house">{base.models.house}</option><option value="apartment">{base.models.apartment}</option><option value="river">{riverCopy[locale].modelName}</option>
        {landmarkIds.map(id => <option key={id} value={id}>{landmarkModels[id].names[locale]}</option>)}
      </select><span>{metadata.revision} · {copy.subtitle}</span>
    </div>
    <main id="main-content">
      <div className="model-page-cache" hidden={page !== '3d'}><div className="landmark-workspace">
        <aside className="landmark-sidebar">
          <section><h2>{copy.parts}</h2><div className="landmark-components">{landmarkGroupIds.map(id => <label key={id}>
            <input type="checkbox" checked={visibility[id]} onChange={event => {
              setVisibility(previous => ({ ...previous, [id]: event.target.checked })); if (selection === id) setSelection(null);
            }} /><span>{copy.groups[id]}</span>
          </label>)}</div><button className="outline-button" onClick={() => { setVisibility(allVisible()); setSelection(null); }}>{copy.showAll}</button></section>
          <section><h2>{copy.environment}</h2><div className="landmark-environment">{(['day', 'night'] as const).map(value => <button key={value} className="outline-button"
            aria-pressed={lighting.environment === value} onClick={() => setLighting(previous => ({ ...previous, environment: value }))}>{copy[value]}</button>)}</div></section>
          <ReferenceCompare key={model} model={model} target={host.current} ready={ready} camera={camera} capture={() => viewer.current?.capture() ?? null}
            restoreCamera={(preset, pose) => { const restored = viewer.current?.restoreCamera(preset, pose) ?? false; if (restored) setCamera(preset); return restored; }}
            onPickingChange={picking => viewer.current?.interaction(!picking)} />
          {model === 'tokyo-tower' ? <section className="landmark-steel-controls"><h2>{copy.steel.title}</h2>
            <label htmlFor="steel-node-choice">{copy.steel.node}</label>
            <select id="steel-node-choice" value={steelNode} disabled={!ready || !steelNodes.length} onChange={event => {
              setSteelNode(event.target.value); if (camera === 'steel-node') viewer.current?.steelNode(event.target.value);
            }}>{steelNodes.map(node => <option key={node.id} value={node.id}>{node.id} · {node.names[locale]}</option>)}</select>
            <button className="outline-button" disabled={!ready || !steelNode || !visibility.structure} onClick={() => {
              setCamera('steel-node'); viewer.current?.steelNode(steelNode);
            }}>{copy.steel.focus}</button>
            <label htmlFor="steel-micro-mode">{copy.steel.micro}</label>
            <select id="steel-micro-mode" value={steelMicro} onChange={event => {
              const value = event.target.value;
              if (value === 'auto' || value === 'on' || value === 'off') { setSteelMicro(value); viewer.current?.steelMicro(value); }
            }}>{(['auto', 'on', 'off'] as const).map(value => <option key={value} value={value}>{copy.steel.modes[value]}</option>)}</select>
            {!visibility.structure ? <p role="status">{copy.steel.hidden}</p> : null}<p>{copy.steel.note}</p>
          </section> : null}
          <section><h2>{copy.dimensions}</h2><dl className="landmark-parameters">
            <div><dt>{copy.height}</dt><dd>{metres(metadata.height)}</dd></div>
            <div><dt>{model === 'tokyo-tower' ? copy.modelGlLevels : copy.levels}</dt><dd>{metadata.levels.map(metres).join(' / ')}</dd></div>
            {'nominalLevels' in metadata ? <div><dt>{copy.nominalLevels}</dt><dd>{metadata.nominalLevels.map(metres).join(' / ')}</dd></div> : null}
          </dl>{model === 'tokyo-tower' ? <p>{copy.glReferenceNote}</p> : null}<a className="landmark-reference" href={metadata.reference} target="_blank" rel="noreferrer">{copy.source} ↗</a>
            {'constructionReference' in metadata ? <p><a className="landmark-reference" href={metadata.constructionReference} target="_blank" rel="noreferrer">{copy.constructionSource} ↗</a></p> : null}</section>
          <p className="landmark-assumption">{'assumptionNotes' in metadata ? metadata.assumptionNotes[locale] : copy.note}</p>
        </aside>
        <section className="landmark-viewer-panel" aria-label={name}>
          <div className="viewer-toolbar"><h1>{name}</h1><div className="toolbar-actions landmark-cameras">{landmarkCameraOptions(model).map(value => <button key={value}
            className="outline-button" aria-pressed={camera === value} disabled={!ready} onClick={() => { setCamera(value); viewer.current?.camera(value); }}>{copy.views[value]}</button>)}</div></div>
          <div className="landmark-canvas" ref={host}>
            {phase === 'loading' ? <img className="landmark-loading-preview" src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(metadata.loadingPreview.svg)}`} alt="" aria-hidden="true" /> : null}
            {phase === 'loading' ? <div className="canvas-message" role="status"><p>{copy.loading}</p>{progress ? <span>{formatDownloadBytes(progress.loaded, locale)}{progress.total ? ` / ${formatDownloadBytes(progress.total, locale)}` : ''}</span> : null}</div> : null}
            {phase === 'error' ? <div className="canvas-message" role="alert"><p>{loadFailureMessage(modelError, locale, copy.error)}</p><button className="outline-button" onClick={() => { setCamera('iso'); setSelection(null); setAttempt(value => value + 1); }}>{copy.retry}</button></div> : null}
            {ready && !landmarkGroupIds.some(id => visibility[id]) ? <p className="canvas-message" role="status">{copy.empty}</p> : null}
            {ready && selection ? <div className="selection-details" role="status" aria-label={copy.selected}><strong>{copy.groups[selection]}</strong>
              <button className="selection-clear" aria-label={copy.clear} onClick={() => setSelection(null)}><X size={16} /></button></div> : null}
          </div>
          <div className="canvas-footer landmark-viewer-footer"><span>{copy.gesture}</span><button className="landmark-download-link" onClick={() => navigate('files')}>{copy.download}</button></div>
        </section>
      </div></div>
      <LandmarkDrawing model={model} kind="plan" active={page === 'plan'} /><LandmarkDrawing model={model} kind="elevation" active={page === 'elevation'} />
      {page === 'files' ? <div className="downloads-page"><header><h1>{name} · {copy.downloads}</h1><p>{metadata.revision} · {copy.original}</p></header>
        <div className="download-list">{landmarkDownloadFiles(model).map(file => <DownloadFile key={file.path} path={file.path} type={file.type}
          title={copy.fileNames[file.id]} detail={copy.fileDetails[file.id]} locale={locale} revision={metadata.revision} download={copy.download}
          compressedStep={file.id === 'step'} metadata={manifest?.[file.id === 'step' ? `${file.path}.gz` : file.path]} manifest={manifest} />)}</div>
        <section className="assumptions"><p>{copy.note}</p><p>{copy.drawingNote}</p></section></div> : null}
    </main>
  </div>;
}
