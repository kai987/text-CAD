import { useEffect, useRef, useState } from 'react';
import { X } from 'lucide-react';
import { useLanguage } from './LanguageContext';
import { useTheme } from './ThemeContext';
import { isLocale, languageNames, locales } from './localization';
import type { Locale } from './localization';
import { isThemePreference } from './theme-preferences';
import { asset, repository } from './data';
import { initialBridgeView, bridgeCameras, bridgeCopy, bridgeDownloads, bridgeGroups, bridgeRevision, bridgeUrl, bridgeViews } from './bridge-copy';
import type { BridgeGroupId, BridgeView } from './bridge-copy';
import type { BridgeViewer } from './bridge-viewer';
import type { ModelProgress } from './model-resource';
import { loadFailureMessage } from './model-load-error';
import { loadDownloadManifest } from './download-resource';
import type { ArtifactManifest } from './download-resource';
import { formatDownloadBytes } from './download-copy';
import DownloadFile from './DownloadFile';
import { riverCopy, residentialUrl, riverUrl } from './river-copy';
import { isLandmarkId, landmarkIds, landmarkModels, landmarkUrl } from './landmark-copy';
import './bridge.css';

const allVisible = () => Object.fromEntries(bridgeGroups.map(id => [id, true])) as Record<BridgeGroupId, boolean>;
type Metadata = { parameters: Record<string, number>; references: { title: string; url: string }[]; assumptions: Record<Locale, string>[] };
function metadataFrom(value: unknown): Metadata {
  if (!value || typeof value !== 'object') throw new Error('Invalid bridge metadata.');
  const data = value as { model_id?: unknown; revision?: unknown; parameters?: unknown; references?: unknown; assumptions?: unknown };
  if (data.model_id !== 'seto-ohashi' || data.revision !== bridgeRevision || !data.parameters || typeof data.parameters !== 'object') throw new Error('Bridge metadata identity does not match.');
  const parameters: Record<string, number> = {};
  for (const key of ['north_length_mm', 'south_length_mm', 'north_main_span_mm', 'south_main_span_mm']) {
    const number = (data.parameters as Record<string, unknown>)[key];
    if (typeof number !== 'number' || !Number.isFinite(number) || number <= 0) throw new Error('Invalid bridge dimension.');
    parameters[key] = number;
  }
  if (!Array.isArray(data.references) || !Array.isArray(data.assumptions)) throw new Error('Missing bridge references.');
  const references = data.references.flatMap(item => {
    if (!item || typeof item !== 'object' || typeof item.title !== 'string' || typeof item.url !== 'string') return [];
    try { if (new URL(item.url).protocol !== 'https:') return []; } catch { return []; }
    return [{ title: item.title, url: item.url }];
  });
  const assumptions = data.assumptions.filter((item): item is Record<Locale, string> => !!item && typeof item === 'object' && locales.every(locale => typeof item[locale] === 'string'));
  return { parameters, references, assumptions };
}
function BridgeDrawing({ kind, active }: { kind: 'plan' | 'elevation' | 'section'; active: boolean }) {
  const { locale } = useLanguage(), copy = bridgeCopy[locale];
  const [phase, setPhase] = useState<'loading' | 'ready' | 'error'>('loading'), [attempt, setAttempt] = useState(0), [zoom, setZoom] = useState(1);
  const source = asset(`output/svg/seto_ohashi_${kind}.svg`), url = attempt ? `${source}${source.includes('?') ? '&' : '?'}retry=${attempt}` : source;
  return <section className="bridge-drawing" hidden={!active} aria-label={copy.tabs[kind]}>
    <div className="viewer-toolbar"><h1>{copy.tabs[kind]}</h1><div className="toolbar-actions">
      <button className="outline-button" disabled={zoom <= 1} onClick={() => setZoom(value => Math.max(1, value - .25))} aria-label={`${copy.tabs[kind]} −`}>−</button>
      <span className="bridge-zoom">{Math.round(zoom * 100)}%</span>
      <button className="outline-button" disabled={zoom >= 4} onClick={() => setZoom(value => Math.min(4, value + .25))} aria-label={`${copy.tabs[kind]} +`}>+</button>
      <button className="outline-button" onClick={() => setZoom(1)}>{copy.reset}</button>
    </div></div><p className="bridge-drawing-note">{copy.drawingNote}</p>
    <div className="bridge-paper-scroll" aria-busy={phase === 'loading'}>
      <img key={attempt} className="bridge-paper" src={url} alt={`${copy.title} · ${copy.tabs[kind]}`} style={{ width: `${zoom * 100}%` }} onLoad={() => setPhase('ready')} onError={() => setPhase('error')} />
      {phase === 'loading' ? <p className="bridge-drawing-status" role="status">{copy.planLoading}</p> : null}
      {phase === 'error' ? <div className="bridge-drawing-status" role="alert"><p>{copy.planError}</p><button className="outline-button" onClick={() => { setPhase('loading'); setAttempt(value => value + 1); }}>{copy.retry}</button></div> : null}
    </div>
  </section>;
}

export default function BridgePage() {
  const { locale, setLocale, copy: base } = useLanguage(), { preference, setPreference, theme } = useTheme(), copy = bridgeCopy[locale];
  const [page, setPage] = useState<BridgeView>(() => initialBridgeView(location.search));
  const [reducedMotion, setReducedMotion] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const [playing, setPlaying] = useState(() => !window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const [waterWaves, setWaterWaves] = useState(true);
  const [night, setNight] = useState(() => new URLSearchParams(location.search).get('environment') === 'night');
  const [visibility, setVisibility] = useState(allVisible), [selection, setSelection] = useState<BridgeGroupId | null>(null);
  const [phase, setPhase] = useState<'loading' | 'ready' | 'error'>('loading'), [modelError, setModelError] = useState<unknown>(null), [progress, setProgress] = useState<ModelProgress | null>(null), [attempt, setAttempt] = useState(0);
  const [manifest, setManifest] = useState<ArtifactManifest | null>(null), [metadata, setMetadata] = useState<Metadata | null>(null), [metadataError, setMetadataError] = useState(false), [metadataAttempt, setMetadataAttempt] = useState(0);
  const host = useRef<HTMLDivElement | null>(null), viewer = useRef<BridgeViewer | null>(null);
  const live = useRef({ theme, night, label: copy.title, visibility, playing, waterWaves }); live.current = { theme, night, label: copy.title, visibility, playing, waterWaves };
  useEffect(() => {
    document.title = `${copy.title} · text-CAD`;
    document.querySelector('meta[name="description"]')?.setAttribute('content', copy.description);
  }, [copy.title, copy.description]);
  useEffect(() => {
    let active = true; setPhase('loading'); setModelError(null); setProgress(null);
    void import('./bridge-viewer').then(({ createBridgeViewer }) => {
      if (!active || !host.current) return;
      const current = live.current, instance = createBridgeViewer(host.current, { theme: current.theme, night: current.night, label: current.label, playing: current.playing, waterWaves: current.waterWaves,
        onReady: () => { if (active) setPhase('ready'); }, onError: error => { if (active) { setModelError(error); setPhase('error'); } },
        onProgress: value => { if (active) setProgress(value); }, onSelection: value => { if (active) setSelection(value); },
      });
      viewer.current = instance; instance.visibility(current.visibility);
    }).catch(error => { if (active) { setModelError(error); setPhase('error'); } });
    return () => { active = false; viewer.current?.dispose(); viewer.current = null; };
  }, [attempt]);
  useEffect(() => { viewer.current?.visibility(visibility); }, [visibility]);
  useEffect(() => { viewer.current?.playing(playing); }, [playing]);
  useEffect(() => { viewer.current?.waterWaves(waterWaves); }, [waterWaves]);
  useEffect(() => {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const change = () => { setReducedMotion(preference.matches); if (preference.matches) setPlaying(false); };
    preference.addEventListener('change', change); return () => preference.removeEventListener('change', change);
  }, []);
  useEffect(() => { viewer.current?.appearance(theme, night); viewer.current?.label(copy.title); }, [theme, night, copy.title]);
  useEffect(() => {
    let active = true;
    void loadDownloadManifest(asset('manifest.json')).then(value => { if (active) setManifest(value); });
    return () => { active = false; };
  }, []);
  useEffect(() => {
    const controller = new AbortController(); setMetadataError(false);
    void fetch(asset('output/review/seto_ohashi_manifest.json'), { signal: controller.signal, cache: metadataAttempt ? 'reload' : 'default' })
      .then(response => { if (!response.ok) throw new Error('Bridge metadata unavailable.'); return response.json(); })
      .then(metadataFrom).then(value => { if (!controller.signal.aborted) setMetadata(value); }).catch(() => { if (!controller.signal.aborted) setMetadataError(true); });
    return () => controller.abort();
  }, [metadataAttempt]);
  function navigate(next: BridgeView) { setPage(next); history.replaceState(null, '', bridgeUrl(location.href, next)); }
  function environment(nextNight: boolean) {
    setNight(nextNight); const url = new URL(location.href); url.searchParams.set('environment', nextNight ? 'night' : 'day'); history.replaceState(null, '', url.href);
  }
  function changeModel(id: string) {
    if (isLandmarkId(id)) location.assign(landmarkUrl(location.href, id, '3d'));
    else if (id === 'river') location.assign(riverUrl(location.href, '3d'));
    else if (id === 'house' || id === 'apartment') location.assign(residentialUrl(location.href, id));
  }
  const ready = phase === 'ready', dimension = (key: string) => metadata ? `${new Intl.NumberFormat(locale).format(metadata.parameters[key] / 1000)} m` : '—';
  return <div className="app-shell bridge-app">
    <a className="skip-link" href="#main-content">{base.app.skip}</a>
    <header className="app-header"><a className="wordmark" href={import.meta.env.BASE_URL} aria-label={base.app.home}>text-CAD</a>
      <nav aria-label={copy.nav}>{bridgeViews.map(id => <button key={id} className={page === id ? 'nav-tab active' : 'nav-tab'} aria-current={page === id ? 'page' : undefined} onClick={() => navigate(id)}>{copy.tabs[id]}</button>)}</nav>
      <div className="header-actions"><label className="theme-control"><span className="sr-only">{base.theme.label}</span><select value={preference} title={base.theme.help} onChange={event => { if (isThemePreference(event.target.value)) setPreference(event.target.value); }}>
        <option value="system">{base.theme.system}</option><option value="light">{base.theme.light}</option><option value="dark">{base.theme.dark}</option></select></label>
        <label className="language-control"><span className="sr-only">{base.app.language}</span><select value={locale} onChange={event => { if (isLocale(event.target.value)) setLocale(event.target.value); }}>{locales.map(id => <option key={id} value={id} lang={id === 'zh' ? 'zh-CN' : id}>{languageNames[id]}</option>)}</select></label>
        <a className="repo-link" href={repository} target="_blank" rel="noreferrer">GitHub</a>
      </div>
    </header>
    <div className="model-switcher"><label htmlFor="model-choice">{copy.modelLabel}</label><select id="model-choice" value="seto-ohashi" onChange={event => changeModel(event.target.value)}>
      <option value="house">{base.models.house}</option><option value="apartment">{base.models.apartment}</option><option value="river">{riverCopy[locale].modelName}</option>
      {landmarkIds.map(id => <option key={id} value={id}>{landmarkModels[id].names[locale]}</option>)}<option value="seto-ohashi">{copy.modelName}</option>
    </select><span>{bridgeRevision}</span></div>
    <main id="main-content">
      <div className="model-page-cache" hidden={page !== '3d'}><div className="bridge-workspace">
        <aside className="bridge-sidebar"><section><h2>{copy.parts}</h2><div className="bridge-components">{bridgeGroups.map(id => <label key={id}><input type="checkbox" checked={visibility[id]} onChange={event => { setVisibility(previous => ({ ...previous, [id]: event.target.checked })); if (!event.target.checked && selection === id) setSelection(null); }} /><span>{copy.groups[id]}</span></label>)}</div>
          <button className="outline-button" onClick={() => { setVisibility(allVisible()); setSelection(null); }}>{copy.showAll}</button></section>
          <section className="bridge-motion-controls"><h2>{copy.motion.title}</h2><p>{copy.motion.note}</p>{reducedMotion ? <p>{copy.motion.reduced}</p> : null}</section>
          <section><h2>{copy.dimensions}</h2><dl className="bridge-parameters">{([['northLength', 'north_length_mm'], ['southLength', 'south_length_mm'], ['northSpan', 'north_main_span_mm'], ['southSpan', 'south_main_span_mm']] as const).map(([label, key]) => <div key={key}><dt>{copy[label]}</dt><dd>{dimension(key)}</dd></div>)}</dl>
            {metadataError ? <p role="status">{copy.metadataError} <button className="outline-button" onClick={() => setMetadataAttempt(value => value + 1)}>{copy.retry}</button></p> : null}</section>
          <section className="bridge-sources"><h2>{copy.source}</h2>{metadata?.references.map(item => <a key={item.url} href={item.url} target="_blank" rel="noreferrer">{item.title}</a>)}</section>
          <p>{copy.note}</p>
          {metadata?.assumptions.length ? <details><summary>{copy.assumptionTitle}</summary><ul>{metadata.assumptions.map((item, index) => <li key={index}>{item[locale]}</li>)}</ul></details> : null}
        </aside>
        <section className="bridge-viewer-panel" aria-label={copy.title}>
          <div className="viewer-toolbar"><h1>{copy.title}</h1><div className="toolbar-actions"><div className="bridge-environment" role="group" aria-label={copy.environment}><button className={night ? 'outline-button' : 'outline-button active'} aria-pressed={!night} onClick={() => environment(false)}>{copy.day}</button><button className={night ? 'outline-button active' : 'outline-button'} aria-pressed={night} onClick={() => environment(true)}>{copy.night}</button></div></div></div>
          <div className="bridge-camera-controls">{bridgeCameras.map(camera => <button key={camera} className="outline-button" disabled={!ready} onClick={() => viewer.current?.camera(camera)}>{copy.cameras[camera]}</button>)}<button className="outline-button bridge-motion-toggle" aria-pressed={playing} disabled={!ready} onClick={() => setPlaying(value => !value)}>{playing ? copy.motion.pause : copy.motion.play}</button><label className="bridge-wave-toggle"><input type="checkbox" checked={waterWaves} disabled={!ready} onChange={event => setWaterWaves(event.target.checked)} />{copy.motion.waves}</label></div>
          <div className="bridge-canvas" ref={host}>
            {phase === 'loading' ? <div className="canvas-message" role="status"><p>{copy.loading}</p>{progress ? <span>{formatDownloadBytes(progress.loaded, locale)}{progress.total ? ` / ${formatDownloadBytes(progress.total, locale)}` : ''}</span> : null}</div> : null}
            {phase === 'error' ? <div className="canvas-message" role="alert"><p>{loadFailureMessage(modelError, locale, copy.error)}</p><button className="outline-button" onClick={() => { setSelection(null); setAttempt(value => value + 1); }}>{copy.retry}</button></div> : null}
            {ready && !bridgeGroups.some(id => visibility[id]) ? <p className="canvas-message" role="status">{copy.empty}</p> : null}
            {ready && selection ? <div className="selection-details" role="status" aria-label={copy.selected}><strong>{copy.groups[selection]}</strong><button className="selection-clear" aria-label={copy.clear} onClick={() => setSelection(null)}><X size={16} /></button></div> : null}
            <div className="canvas-footer"><span>{copy.gesture}</span><button className="bridge-download-link" onClick={() => navigate('files')}>{copy.download}</button></div>
          </div><p className="bridge-lighting-note">{copy.nightNote}</p>
        </section>
      </div></div>
      <BridgeDrawing kind="plan" active={page === 'plan'} /><BridgeDrawing kind="elevation" active={page === 'elevation'} /><BridgeDrawing kind="section" active={page === 'section'} />
      {page === 'files' ? <div className="downloads-page"><header><h1>{copy.downloads}</h1><p>{bridgeRevision} · {copy.original}</p></header>
        <div className="download-list">{bridgeDownloads.map(file => <DownloadFile key={file.path} path={file.path} type={file.type} locale={locale} title={copy.fileNames[file.id]} detail={copy.fileDetails[file.id]} revision={bridgeRevision} download={copy.download} metadata={manifest?.[file.path]} />)}</div><section className="assumptions"><p>{copy.note}</p><p>{copy.drawingNote}</p></section>
      </div> : null}
    </main>
  </div>;
}
