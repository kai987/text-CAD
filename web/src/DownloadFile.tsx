import { useEffect, useRef, useState } from 'react';
import { Download } from 'lucide-react';
import { asset } from './data';
import type { Locale } from './localization';
import { downloadResource, DownloadError, requireDownloadMetadata } from './download-resource';
import type { ArtifactMetadata, DownloadErrorCode, DownloadProgress } from './download-resource';
import { downloadCopy, downloadErrorText, downloadProgressText, formatDownloadBytes } from './download-copy';

type DownloadState =
  | { phase: 'idle' | 'starting' | 'processing' | 'saved' | 'cancelled' }
  | { phase: 'downloading'; progress: DownloadProgress }
  | { phase: 'failed'; code: DownloadErrorCode; status?: number };

export interface DownloadFileProps {
  path: string; title: string; detail: string; type: string;
  download: string; locale: Locale; revision: string;
  metadata?: ArtifactMetadata; compressedStep?: boolean;
}

export default function DownloadFile({ path, title, detail, type, download, locale, revision, metadata, compressedStep = false }: DownloadFileProps) {
  const [state, setState] = useState<DownloadState>({ phase: 'idle' });
  const active = useRef<AbortController | null>(null);
  useEffect(() => () => { active.current?.abort(); active.current = null; }, []);
  const href = asset(compressedStep ? `${path}.gz` : path);
  const copy = downloadCopy[locale];
  const busy = state.phase === 'starting' || state.phase === 'downloading' || state.phase === 'processing';
  async function start() {
    if (active.current) return;
    const controller = new AbortController();
    active.current = controller;
    setState({ phase: 'starting' });
    try {
      // A fast click can precede the list's metadata fetch. Await that shared
      // request so the first download gets the same integrity checks as a retry.
      const entry = await requireDownloadMetadata(asset('manifest.json'), compressedStep ? `${path}.gz` : path, metadata);
      if (controller.signal.aborted || active.current !== controller) throw controller.signal.reason;
      const blob = await downloadResource({ url: href, type, compressedStep, metadata: entry, signal: controller.signal,
        onProgress: progress => { if (active.current === controller) setState({ phase: 'downloading', progress }); },
        onProcessing: () => { if (active.current === controller) setState({ phase: 'processing' }); },
      });
      if (controller.signal.aborted || active.current !== controller) return;
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url; link.download = path.split('/').at(-1)!;
      document.body.append(link); link.click(); link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 30_000);
      setState({ phase: 'saved' });
    } catch (error) {
      if (active.current !== controller) return;
      if (controller.signal.aborted) setState({ phase: 'cancelled' });
      else setState({ phase: 'failed', code: error instanceof DownloadError ? error.code : 'network',
        status: error instanceof DownloadError ? error.status : undefined });
    } finally { if (active.current === controller) active.current = null; }
  }
  const status = state.phase === 'downloading' ? downloadProgressText(state.progress, locale)
    : state.phase === 'idle' || state.phase === 'failed' ? '' : copy[state.phase];
  const decodedBytes = compressedStep ? metadata?.decodedBytes : metadata?.bytes;
  return <div className="download-file" data-file={path}>
    <a className="download-row" href={href} download aria-busy={busy} aria-disabled={busy || undefined} onClick={event => {
      // Preserve the native gzip download on browsers without decompression.
      if (compressedStep && typeof DecompressionStream === 'undefined') return;
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault(); void start();
    }}>
      <span className="file-type">{type}</span>
      <span className="file-description"><strong>{title}</strong><span>{detail}</span>
        <span className="download-metadata">{revision}{decodedBytes ? ` · ${copy.size} ${formatDownloadBytes(decodedBytes, locale)}` : ''}
          {compressedStep && metadata ? ` · ${copy.transfer} ${formatDownloadBytes(metadata.bytes, locale)}` : ''}</span>
      </span>
      <Download size={20} aria-hidden="true" /><span className="sr-only">{download}</span>
    </a>
    {state.phase !== 'idle' ? <div className="download-status">
      {state.phase === 'failed' ? <p role="alert">{downloadErrorText(state.code, state.status, locale)}</p>
        : <p role="status" aria-live="polite">{status}</p>}
      {state.phase === 'downloading' ? <progress aria-label={`${download}: ${title}`} max={state.progress.total ?? undefined}
        value={state.progress.total ? Math.min(state.progress.loaded, state.progress.total) : undefined} /> : null}
      <div className="download-actions">
        {busy ? <button className="outline-button" onClick={() => {
          const controller = active.current; active.current = null;
          controller?.abort(); setState({ phase: 'cancelled' });
        }}>{copy.cancel}</button> : null}
        {state.phase === 'failed' || state.phase === 'cancelled' ? <button className="outline-button" onClick={() => void start()}>{copy.retry}</button> : null}
        {state.phase === 'failed' && compressedStep ? <a className="outline-button" href={href} download>{copy.compressed}</a> : null}
      </div>
    </div> : null}
  </div>;
}
