import { useState } from 'react';
import { repository } from './data';
import { initialPage, settingsForPreset } from './model-state';
import type { PageId } from './model-state';
import ModelPage from './ModelPage';
import PlanPage from './PlanPage';
import DownloadPage from './DownloadPage';
import { useLanguage } from './LanguageContext';
import { isLocale, languageNames, locales } from './localization';

const tabs: PageId[] = ['3d', '1f', '2f', 'files'];

export default function App() {
  const { locale, setLocale, copy } = useLanguage();
  const [page, setPage] = useState(() => initialPage(location.search));
  const [settings, setSettings] = useState(() => {
    const mode = new URLSearchParams(location.search).get('mode');
    return settingsForPreset(mode === 'first' || mode === 'second' ? mode : 'exterior');
  });
  function navigate(next: PageId) {
    setPage(next);
    const url = new URL(location.href);
    url.search = ''; url.searchParams.set('view', next);
    history.replaceState(null, '', url);
  }
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">{copy.app.skip}</a>
    <header className="app-header">
      <a className="wordmark" href={import.meta.env.BASE_URL} aria-label={copy.app.home}>text-CAD</a>
      <nav aria-label={copy.app.nav}>
        {tabs.map(id => <button key={id} type="button" className={page === id ? 'nav-tab active' : 'nav-tab'}
          aria-current={page === id ? 'page' : undefined} onClick={() => navigate(id)}>{copy.app.tabs[id]}</button>)}
      </nav>
      <div className="header-actions">
        <label className="language-control">
          <span className="sr-only">{copy.app.language}</span>
          <select value={locale} onChange={event => {
            if (isLocale(event.target.value)) setLocale(event.target.value);
          }}>
            {locales.map(id => <option key={id} value={id} lang={id === 'zh' ? 'zh-CN' : id}>{languageNames[id]}</option>)}
          </select>
        </label>
        <a className="repo-link" href={repository} target="_blank" rel="noreferrer">GitHub</a>
      </div>
    </header>
    <main id="main-content">
      {page === '3d' ? <ModelPage settings={settings} setSettings={setSettings} /> :
        page === '1f' || page === '2f' ? <PlanPage key={page} floor={page === '1f' ? 1 : 2} /> : <DownloadPage />}
    </main>
  </div>;
}
