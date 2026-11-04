import { useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { Download } from 'lucide-react';
import { asset, assetSha256 } from './data';
import { artifactDownloadRequests } from './asset-url';
import type { Locale } from './localization';
import { downloadResource, DownloadError, requireDownloadTransport } from './download-resource';
import type { ArtifactMetadata, ArtifactManifest, DownloadErrorCode, DownloadProgress } from './download-resource';
import { hasDecodedIntegrity, selectDownloadTransport } from './download-transport';
import { downloadCopy, downloadErrorText, downloadProgressText, formatDownloadBytes } from './download-copy';

type DownloadState =
  | { phase: 'idle' | 'starting' | 'processing' | 'saved' | 'cancelled' }
  | { phase: 'downloading'; progress: DownloadProgress }
  | { phase: 'failed'; code: DownloadErrorCode; status?: number };

export interface DownloadFileProps {
  path: string; title: string; detail: string; type: string;
  download: string; locale: Locale; revision: string;
  metadata?: ArtifactMetadata; compressedStep?: boolean;
  manifest?: ArtifactManifest | null;
  compact?: boolean; className?: string; children?: ReactNode;
}

export default function DownloadFile({ path, title, detail, type, download, locale, revision, metadata, manifest, compressedStep = false, compact = false, className, children }: DownloadFileProps) {
  const [state, setState] = useState<DownloadState>({ phase: 'idle' });
  const active = useRef<AbortController | null>(null);
  useEffect(() => () => { active.current?.abort(); active.current = null; }, []);
  const selected = manifest ? selectDownloadTransport(path, manifest, compressedStep) : null;
  const chunked = selected?.metadata.transport === 'chunks';
  const gzip = selected?.compression === 'gzip' || compressedStep || metadata?.transport === 'gzip'
    || hasDecodedIntegrity(metadata) || Boolean(assetSha256(`${path}.gz`));
  const href = selected ? artifactDownloadRequests(selected, asset).url : asset(gzip ? `${path}.gz` : path);
  const copy = downloadCopy[locale];
  const busy = state.phase === 'starting' || state.phase === 'downloading' || state.phase === 'processing';
  async function start(saveCompressed = false) {
    if (active.current) return;
    const controller = new AbortController();
    active.current = controller;
    setState({ phase: 'starting' });
    try {
      // A fast click can precede the list's metadata fetch. Await that shared
      // request so the first download gets the same integrity checks as a retry.
      const transfer = await requireDownloadTransport(asset('manifest.json'), path, { manifest, known: metadata, compressedStep });
      if (controller.signal.aborted || active.current !== controller) throw controller.signal.reason;
      const blob = await downloadResource({ ...artifactDownloadRequests(transfer, asset), type, compression: transfer.compression,
        compressedStep, decompress: !saveCompressed, metadata: transfer.metadata, signal: controller.signal,
        onProgress: progress => { if (active.current === controller) setState({ phase: 'downloading', progress }); },
        onProcessing: () => { if (active.current === controller) setState({ phase: 'processing' }); },
      });
      if (controller.signal.aborted || active.current !== controller) return;
      const magic = new Uint8Array(await blob.slice(0, 2).arrayBuffer());
      if (controller.signal.aborted || active.current !== controller) return;
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url; link.download = path.split('/').at(-1)! + (magic[0] === 0x1f && magic[1] === 0x8b ? '.gz' : '');
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
  const displayMetadata = selected?.metadata ?? metadata;
  const decodedBytes = hasDecodedIntegrity(displayMetadata) ? displayMetadata.decodedBytes : displayMetadata?.bytes;
  const row = <>
    <span className="file-type">{type}</span>
    <span className="file-description"><strong>{title}</strong><span>{detail}</span>
      <span className="download-metadata">{revision}{decodedBytes ? ` · ${copy.size} ${formatDownloadBytes(decodedBytes, locale)}` : ''}
        {gzip && hasDecodedIntegrity(displayMetadata) ? ` · ${copy.transfer} ${formatDownloadBytes(displayMetadata.bytes, locale)}` : ''}</span>
    </span>
    <Download size={20} aria-hidden="true" /><span className="sr-only">{download}</span>
  </>;
  return <div className="download-file" data-file={path} style={compact ? { display: 'contents' } : undefined}>
    {compact ? <a className={className} href={href} download aria-busy={busy} aria-disabled={busy || undefined}
      onClick={event => {
        event.preventDefault(); void start(gzip && typeof DecompressionStream === 'undefined');
      }}>{children ?? title}</a> : !selected || chunked ? <button type="button" className="download-row" aria-busy={busy} disabled={busy}
      onClick={() => void start(gzip && typeof DecompressionStream === 'undefined')}>{row}</button>
      : <a className="download-row" href={href} download aria-busy={busy} aria-disabled={busy || undefined} onClick={event => {
      // Preserve the native gzip download on browsers without decompression.
      if (gzip && typeof DecompressionStream === 'undefined') return;
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault(); void start();
    }}>{row}</a>}
    {state.phase !== 'idle' ? <div className="download-status" style={compact ? { pointerEvents: 'auto', padding: '4px 0', minWidth: 0, maxWidth: 240 } : undefined}>
      {state.phase === 'failed' ? <p role="alert">{downloadErrorText(state.code, state.status, locale)}</p>
        : <p role="status" aria-live="polite">{status}</p>}
      {state.phase === 'downloading' ? <progress aria-label={`${download}: ${title}`} max={state.progress.total ?? undefined}
        value={state.progress.total ? Math.min(state.progress.loaded, state.progress.total) : undefined} /> : null}
      <div className="download-actions">
        {busy ? <button className="outline-button" onClick={() => {
          const controller = active.current; active.current = null;
          controller?.abort(); setState({ phase: 'cancelled' });
        }}>{copy.cancel}</button> : null}
        {state.phase === 'failed' || state.phase === 'cancelled' ? <button className="outline-button"
          onClick={() => void start(gzip && typeof DecompressionStream === 'undefined')}>{copy.retry}</button> : null}
        {state.phase === 'failed' && gzip ? (!selected || chunked
          ? <button className="outline-button" onClick={() => void start(true)}>{copy.compressed}</button>
          : <a className="outline-button" href={href} download>{copy.compressed}</a>) : null}
      </div>
    </div> : null}
  </div>;
}
