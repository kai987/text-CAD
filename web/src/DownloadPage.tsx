import { ArrowUpRight, Download } from 'lucide-react';
import { asset, repository } from './data';
import { useModel } from './ModelContext';
import { format } from './localization';
import StructuralOptions from './StructuralOptions';

export default function DownloadPage() {
  const { copy, data, downloads, source, layout } = useModel();
  return <div className="downloads-page">
    <header><h1>{copy.downloads.title}</h1><p>{format(copy.downloads.revision, { drawing: data.drawingRevision, model: data.modelRevision })}</p></header>
    {layout.id === 'house' ? <StructuralOptions /> : null}
    <div className="download-list">
      {downloads.map(f => <a className="download-row" key={f.path} href={asset(f.path)} download>
        <span className="file-type">{f.type}</span><span className="file-description"><strong>{copy.downloads.files[f.id].title}</strong><span>{copy.downloads.files[f.id].detail}</span></span>
        <Download size={20} aria-hidden="true" /><span className="sr-only">{copy.downloads.download}</span>
      </a>)}
    </div>
    <div className="source-links">
    <a className="outline-button source-button" href={`${repository}/blob/main/${source}`} target="_blank" rel="noreferrer">{copy.downloads.source}<ArrowUpRight size={17} aria-hidden="true" /></a>
    {layout.id === 'house' ? <a className="outline-button source-button" href={`${repository}/tree/main/src/lib`} target="_blank" rel="noreferrer">{copy.downloads.sourceParameters}<ArrowUpRight size={17} aria-hidden="true" /></a> : null}
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
