import { useEffect, useRef, useState } from 'react';
import { RotateCcw, View, X } from 'lucide-react';
import { useLanguage } from './LanguageContext';
import { useTheme } from './ThemeContext';
import { isLocale, languageNames, locales } from './localization';
import { isThemePreference } from './theme-preferences';
import { asset, repository } from './data';
import { initialRiverView, residentialUrl, riverCopy, riverDownloadFiles, riverGroups, riverUrl, riverViews } from './river-copy';
import type { RiverGroupId, RiverView } from './river-copy';
import type { RiverViewer } from './river-viewer';
import type { ModelProgress } from './model-resource';
import { loadDownloadManifest } from './download-resource';
import type { ArtifactManifest } from './download-resource';
import DownloadFile from './DownloadFile';
import { formatDownloadBytes } from './download-copy';
import riverData from './river-data.json';
import './river.css';

const groupIds = Object.keys(riverGroups) as RiverGroupId[];
const allVisible = () => Object.fromEntries(groupIds.map(id => [id, true])) as Record<RiverGroupId, boolean>;

function RiverDrawing({ kind, active }: { kind: 'plan' | 'section'; active: boolean }) {
  const { locale } = useLanguage();
  const copy = riverCopy[locale];
  const [phase, setPhase] = useState<'loading' | 'ready' | 'error'>('loading');
  const [attempt, setAttempt] = useState(0);
  const [zoom, setZoom] = useState(1);
  const path = `output/svg/river_demo_${kind}.svg`;
  const source = asset(path);
  const drawingUrl = attempt ? `${source}${source.includes('?') ? '&' : '?'}retry=${attempt}` : source;
  return <section className="river-drawing" hidden={!active} aria-label={copy.tabs[kind]}>
    <div className="viewer-toolbar"><h1>{copy.tabs[kind]}</h1><div className="toolbar-actions">
      <button className="outline-button" onClick={() => setZoom(value => Math.max(1, value - 0.25))} disabled={zoom <= 1} aria-label={`${copy.tabs[kind]} −`}>−</button>
      <span className="river-zoom">{Math.round(zoom * 100)}%</span>
      <button className="outline-button" onClick={() => setZoom(value => Math.min(3, value + 0.25))} disabled={zoom >= 3} aria-label={`${copy.tabs[kind]} +`}>+</button>
      <button className="outline-button" onClick={() => setZoom(1)}>{copy.reset}</button>
    </div></div>
    <p className="river-drawing-note">{copy.drawingNote}</p>
    <div className="river-paper-scroll" aria-busy={phase === 'loading'}>
      <img key={attempt} className="river-paper" src={drawingUrl} alt={kind === 'plan' ? copy.planAlt : copy.sectionAlt}
        style={{ width: `${zoom * 100}%` }} onLoad={() => setPhase('ready')} onError={() => setPhase('error')} />
      {phase === 'loading' ? <p className="river-drawing-status" role="status">{copy.planLoading}</p> : null}
      {phase === 'error' ? <div className="river-drawing-status" role="alert"><p>{copy.planError}</p><button className="outline-button" onClick={() => {
        setPhase('loading'); setAttempt(value => value + 1);
      }}>{copy.retry}</button></div> : null}
    </div>
  </section>;
}

export default function RiverPage() {
  const { locale, setLocale, copy: base } = useLanguage();
  const { preference, setPreference, theme } = useTheme();
  const copy = riverCopy[locale];
  const [page, setPage] = useState<RiverView>(() => initialRiverView(location.search));
  const formatDimension = (value: number) => new Intl.NumberFormat(locale, { maximumFractionDigits: 0 }).format(value);
  const [visibility, setVisibility] = useState(allVisible);
  const [selection, setSelection] = useState<RiverGroupId | null>(null);
  const [phase, setPhase] = useState<'loading' | 'ready' | 'error'>('loading');
  const [progress, setProgress] = useState<ModelProgress | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [manifest, setManifest] = useState<ArtifactManifest | null>(null);
  const host = useRef<HTMLDivElement | null>(null);
  const viewer = useRef<RiverViewer | null>(null);
  const live = useRef({ theme, label: copy.title, visibility });
  live.current = { theme, label: copy.title, visibility };
  useEffect(() => {
    document.title = `${copy.title} · text-CAD`;
    document.querySelector('meta[name="description"]')?.setAttribute('content', copy.description);
  }, [copy.title, copy.description]);
  useEffect(() => {
    let active = true;
    setPhase('loading'); setProgress(null);
    void import('./river-viewer').then(({ createRiverViewer }) => {
      if (!active || !host.current) return;
      const current = live.current;
      const instance = createRiverViewer(host.current, { theme: current.theme, label: current.label,
        onReady: () => { if (active) setPhase('ready'); },
        onError: () => { if (active) setPhase('error'); },
        onProgress: value => { if (active) setProgress(value); },
        onSelection: value => { if (active) setSelection(value); },
      });
      viewer.current = instance;
      instance.visibility(current.visibility);
    }).catch(() => { if (active) setPhase('error'); });
    return () => { active = false; viewer.current?.dispose(); viewer.current = null; };
  }, [attempt]);
  useEffect(() => { viewer.current?.visibility(visibility); }, [visibility]);
  useEffect(() => { viewer.current?.theme(theme); viewer.current?.label(copy.title); }, [theme, copy.title]);
  useEffect(() => {
    let active = true;
    void loadDownloadManifest(asset('manifest.json')).then(value => { if (active) setManifest(value); });
    return () => { active = false; };
  }, []);
  function navigate(next: RiverView) { setPage(next); history.replaceState(null, '', riverUrl(location.href, next)); }
  function changeModel(id: string) {
    if (id === 'house' || id === 'apartment') location.assign(residentialUrl(location.href, id));
  }
  const ready = phase === 'ready';
  return <div className="app-shell river-app">
    <a className="skip-link" href="#main-content">{base.app.skip}</a>
    <header className="app-header">
      <a className="wordmark" href={import.meta.env.BASE_URL} aria-label={base.app.home}>text-CAD</a>
      <nav aria-label={copy.nav}>{riverViews.map(id => <button key={id} className={page === id ? 'nav-tab active' : 'nav-tab'}
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
      <select id="model-choice" value="river" onChange={event => changeModel(event.target.value)}>
        <option value="house">{base.models.house}</option><option value="apartment">{base.models.apartment}</option><option value="river">{copy.modelName}</option>
      </select><span>{riverData.revision} · {copy.parameterNote}</span>
    </div>
    <main id="main-content">
      {/* All three visual assets start loading on entry; hidden drawing and model views retain their state. */}
      <div className="model-page-cache" hidden={page !== '3d'}>
        <div className="river-workspace">
          <aside className="river-sidebar">
            <section><h2>{copy.parts}</h2><div className="river-component-list">{groupIds.map(id => <label key={id}>
              <input type="checkbox" checked={visibility[id]} onChange={event => {
                setVisibility(previous => ({ ...previous, [id]: event.target.checked }));
                if (!event.target.checked && selection === id) setSelection(null);
              }} /><span>{copy.groups[id]}</span>
            </label>)}</div><button className="outline-button" onClick={() => { setVisibility(allVisible()); setSelection(null); }}>{copy.showAll}</button></section>
            <section><h2>{copy.dimensions}</h2><dl className="river-parameters">
              <div><dt>{copy.units}</dt><dd>{riverData.units}</dd></div><div><dt>{copy.length}</dt><dd>{formatDimension(riverData.parameters.length)}</dd></div>
              <div><dt>{copy.width}</dt><dd>{formatDimension(riverData.parameters.width)}</dd></div><div><dt>{copy.waterWidth}</dt><dd>{formatDimension(riverData.parameters.water_width)}</dd></div>
              <div><dt>{copy.bridgeSpan}</dt><dd>{formatDimension(riverData.bridge.span)}</dd></div>
            </dl><p>{copy.parameterNote}</p></section>
            <p className="river-assumption">{copy.note}</p>
          </aside>
          <section className="river-viewer-panel" aria-label={copy.title}>
            <div className="viewer-toolbar"><h1>{copy.title}</h1><div className="toolbar-actions">
              <button className="outline-button" disabled={!ready} onClick={() => viewer.current?.camera('top')}><View size={16} aria-hidden="true" />{copy.top}</button>
              <button className="outline-button" disabled={!ready} onClick={() => viewer.current?.camera('iso')}><RotateCcw size={16} aria-hidden="true" />{copy.reset}</button>
            </div></div>
            <div className="river-canvas" ref={host}>
              {phase === 'loading' ? <div className="canvas-message" role="status"><p>{copy.loading}</p>{progress ? <span>{formatDownloadBytes(progress.loaded, locale)}{progress.total ? ` / ${formatDownloadBytes(progress.total, locale)}` : ''}</span> : null}</div> : null}
              {phase === 'error' ? <div className="canvas-message" role="alert"><p>{copy.error}</p><button className="outline-button" onClick={() => { setSelection(null); setAttempt(value => value + 1); }}>{copy.retry}</button></div> : null}
              {ready && !groupIds.some(id => visibility[id]) ? <p className="canvas-message" role="status">{copy.empty}</p> : null}
              {ready && selection ? <div className="selection-details" role="status" aria-label={copy.selected}><strong>{copy.groups[selection]}</strong>
                <button className="selection-clear" aria-label={copy.clear} onClick={() => setSelection(null)}><X size={16} /></button></div> : null}
              <div className="canvas-footer"><span>{copy.gesture}</span><button className="river-download-link" onClick={() => navigate('files')}>{copy.download}</button></div>
            </div>
          </section>
        </div>
      </div>
      <RiverDrawing kind="plan" active={page === 'plan'} /><RiverDrawing kind="section" active={page === 'section'} />
      {page === 'files' ? <div className="downloads-page">
        <header><h1>{copy.downloads}</h1><p>{riverData.revision} · {copy.original}</p></header>
        <div className="download-list">{riverDownloadFiles.map(file => <DownloadFile key={file.path} path={file.path} type={file.type} locale={locale}
          title={copy.fileNames[file.id]} detail={copy.fileDetails[file.id]} revision={riverData.revision} download={copy.download} metadata={manifest?.[file.path]} />)}</div>
        <section className="assumptions"><p>{copy.note}</p><p>{copy.drawingNote}</p></section>
      </div> : null}
    </main>
  </div>;
}
