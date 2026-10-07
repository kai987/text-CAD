import { useState } from 'react';
import { Download } from 'lucide-react';
import { decodedStep } from './step-download';
import { asset } from './data';

export default function StepDownload({ path, title, detail, download, errorText }: {
  path: string; title: string; detail: string; download: string; errorText: string;
}) {
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const href = asset(`${path}.gz`);
  return <div>
    <a className="download-row" href={href} download aria-busy={busy} onClick={async event => {
      if (typeof DecompressionStream === 'undefined') return;
      event.preventDefault();
      if (busy) return;
      setBusy(true); setFailed(false);
      try {
        const blob = await decodedStep(href);
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url; link.download = path.split('/').at(-1)!;
        document.body.append(link); link.click(); link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 30000);
      } catch { setFailed(true); }
      finally { setBusy(false); }
    }}>
      <span className="file-type">STEP</span><span className="file-description"><strong>{title}</strong><span>{detail}</span></span>
      <Download size={20} aria-hidden="true" /><span className="sr-only">{download}</span>
    </a>
    {failed ? <p role="alert"><a href={href} download>{errorText}</a></p> : null}
  </div>;
}
