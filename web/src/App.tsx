import { useState } from 'react';
import { repository } from './data';
import { initialPage, settingsForPreset } from './model-state';
import type { PageId } from './model-state';
import ModelPage from './ModelPage';
import PlanPage from './PlanPage';
import DownloadPage from './DownloadPage';
import { useLanguage } from './LanguageContext';
import { isLocale, languageNames, locales } from './localization';
import { useTheme } from './ThemeContext';
import { isThemePreference } from './theme-preferences';

const tabs: PageId[] = ['3d', '1f', '2f', 'files'];

export default function App() {
  const { locale, setLocale, copy } = useLanguage();
  const { preference, setPreference } = useTheme();
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
        <label className="theme-control">
          <span className="sr-only">{copy.theme.label}</span>
          <select value={preference} title={copy.theme.help} onChange={event => {
            if (isThemePreference(event.target.value)) setPreference(event.target.value);
          }}>
            <option value="system">{copy.theme.system}</option>
            <option value="light">{copy.theme.light}</option>
            <option value="dark">{copy.theme.dark}</option>
          </select>
        </label>
        <label className="language-control">
          <span className="sr-only">{copy.app.language}</span>
          <select value={locale} onChange={event => {
            if (isLocale(event.target.value)) setLocale(event.target.value);
          }}>
            {locales.map(id => <option key={id} value={id} lang={id === 'zh' ? 'zh-CN' : id}>{languageNames[id]}</option>)}
          </select>
        </label>
        <a className="repo-link" href={repository} target="_blank" rel="noreferrer" aria-label="GitHub">
          <svg className="repo-icon" width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .75a11.25 11.25 0 0 0-3.56 21.92c.56.1.77-.24.77-.54v-2.1c-3.14.68-3.8-1.33-3.8-1.33-.52-1.3-1.25-1.65-1.25-1.65-1.03-.7.08-.69.08-.69 1.14.08 1.74 1.17 1.74 1.17 1.01 1.74 2.65 1.24 3.3.95.1-.74.4-1.24.72-1.52-2.5-.28-5.13-1.25-5.13-5.56 0-1.23.44-2.24 1.16-3.03-.12-.28-.5-1.43.11-2.98 0 0 .95-.3 3.1 1.16a10.79 10.79 0 0 1 5.64 0c2.15-1.46 3.1-1.16 3.1-1.16.61 1.55.23 2.7.11 2.98.72.79 1.16 1.8 1.16 3.03 0 4.32-2.64 5.28-5.15 5.56.4.35.76 1.03.76 2.09v3.08c0 .3.2.65.78.54A11.25 11.25 0 0 0 12 .75Z" /></svg><span className="repo-label">GitHub</span>
        </a>
      </div>
    </header>
    <main id="main-content">
      {page === '3d' ? <ModelPage settings={settings} setSettings={setSettings} /> :
        page === '1f' || page === '2f' ? <PlanPage key={page} floor={page === '1f' ? 1 : 2} /> : <DownloadPage />}
    </main>
  </div>;
}
