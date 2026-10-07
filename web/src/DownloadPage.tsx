import { useEffect, useState } from 'react';
import { ArrowUpRight } from 'lucide-react';
import { asset, sourceUrl } from './data';
import { useModel } from './ModelContext';
import { format } from './localization';
import StructuralOptions from './StructuralOptions';
import StepDownload from './StepDownload';
import DownloadFile from './DownloadFile';
import { useLanguage } from './LanguageContext';
import { loadDownloadManifest } from './download-resource';
import type { ArtifactManifest } from './download-resource';

export default function DownloadPage() {
  const { copy, data, downloads, source, layout } = useModel();
  const { locale } = useLanguage();
  const [manifest, setManifest] = useState<ArtifactManifest | null>(null);
  useEffect(() => {
    let mounted = true;
    void loadDownloadManifest(asset('manifest.json')).then(value => { if (mounted) setManifest(value); });
    return () => { mounted = false; };
  }, []);
  const revisions = { drawing: data.drawingRevision, model: data.modelRevision };
  return <div className="downloads-page">
    <header><h1>{copy.downloads.title}</h1><p>{format(copy.downloads.revision, revisions)}</p></header>
    {layout.id === 'house' ? <StructuralOptions /> : null}
    <div className="download-list">
      {downloads.map(f => {
        const props = { path: f.path, title: copy.downloads.files[f.id].title,
          detail: format(copy.downloads.files[f.id].detail, revisions), download: copy.downloads.download,
          locale, revision: f.type === 'GLB' || f.type === 'STEP' ? data.modelRevision : data.drawingRevision,
          metadata: manifest?.[f.path === 'STEP/house_3d.step' ? `${f.path}.gz` : f.path] };
        return f.path === 'STEP/house_3d.step' ? <StepDownload key={f.path} {...props} />
          : <DownloadFile key={f.path} {...props} type={f.type} />;
      })}
    </div>
    <div className="source-links">
    <a className="outline-button source-button" href={sourceUrl(source)} target="_blank" rel="noreferrer">{copy.downloads.source}<ArrowUpRight size={17} aria-hidden="true" /></a>
    {layout.id === 'house' ? <a className="outline-button source-button" href={sourceUrl('src/lib', 'tree')} target="_blank" rel="noreferrer">{copy.downloads.sourceParameters}<ArrowUpRight size={17} aria-hidden="true" /></a> : null}
    </div>
    <section className="assumptions"><h2>{copy.downloads.notes}</h2>
      <p>{copy.downloads.summary}</p>
      <p>{copy.downloads.drafting}</p>
      <p>{copy.downloads.originalNote}</p>
      <details className="assumption-details"><summary>{copy.downloads.assumptionsTitle}</summary>
        <ol>{copy.assumptions.map((assumption, index) => <li key={index}>{assumption}</li>)}</ol>
      </details>
    </section>
  </div>;
}
