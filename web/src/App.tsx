import { useState } from 'react';
import { repository } from './data';
import { initialPage, settingsForPreset } from './model-state';
import type { PageId } from './model-state';
import ModelPage from './ModelPage';
import PlanPage from './PlanPage';
import DownloadPage from './DownloadPage';

const tabs: { id: PageId; label: string }[] = [
  { id: '3d', label: '三维模型' }, { id: '1f', label: '一层平面' },
  { id: '2f', label: '二层平面' }, { id: 'files', label: '文件下载' },
];

export default function App() {
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
    <a className="skip-link" href="#main-content">跳到查看区域</a>
    <header className="app-header">
      <a className="wordmark" href={import.meta.env.BASE_URL} aria-label="text-CAD 首页">text-CAD</a>
      <nav aria-label="房屋模型与图纸">
        {tabs.map(t => <button key={t.id} type="button" className={page === t.id ? 'nav-tab active' : 'nav-tab'}
          aria-current={page === t.id ? 'page' : undefined} onClick={() => navigate(t.id)}>{t.label}</button>)}
      </nav>
      <a className="repo-link" href={repository} target="_blank" rel="noreferrer">GitHub</a>
    </header>
    <main id="main-content">
      {page === '3d' ? <ModelPage settings={settings} setSettings={setSettings} /> :
        page === '1f' || page === '2f' ? <PlanPage key={page} floor={page === '1f' ? 1 : 2} /> : <DownloadPage />}
    </main>
  </div>;
}
