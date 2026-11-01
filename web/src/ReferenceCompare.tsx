import { useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { assetSha256 } from './data';
import { useLanguage } from './LanguageContext';
import { landmarkModels } from './landmark-copy';
import type { LandmarkCamera, LandmarkId } from './landmark-copy';
import { defaultReferenceAlignment, referenceAlignment, referenceImageRect, referenceLimits, referenceTransform, validReferenceImage, validReferenceDimensions } from './reference-review';
import type { ReferenceAlignment } from './reference-review';

const messages = {
  ja: { title: '写真と比較', file: '参考画像を選択', note: '画像は端末内で処理され、送信されません。正面・側面の視点から、位置と大きさを合わせて確認できます。', limit: 'PNG・JPEG・WebP、12 MBまで。', invalid: '画像を読み込めません。PNG・JPEG・WebP（12 MB以下）を選んでください。', visible: '画像を重ねる', opacity: '画像の不透明度', scale: '画像の倍率', x: '左右の位置', y: '上下の位置', rotation: '画像の回転', reset: '位置をリセット', remove: '画像を外す', record: '比較条件を保存', png: '比較画像を保存', caution: '写真の遠近感やレンズの差は補正していません。外観の目視比較用で、実測や構造の検証ではありません。', controls: '比較用の高さ基準', model: 'モデルGL', official: '公式案内高さ', source: '写真の出典・撮影条件（任意）', failed: '保存できませんでした。もう一度お試しください。' },
  zh: { title: '照片对比', file: '选择参考图片', note: '图片仅在本机处理，不会上传。可用正面或侧面视角调整位置与大小后对比。', limit: 'PNG、JPEG、WebP，最大12 MB。', invalid: '无法读取图片。请选择12 MB以内的PNG、JPEG或WebP。', visible: '叠加参考图片', opacity: '图片不透明度', scale: '图片缩放', x: '左右位置', y: '上下位置', rotation: '图片旋转', reset: '重置位置', remove: '移除图片', record: '保存对比条件', png: '保存对比图片', caution: '尚未校正照片透视与镜头差异。仅供外观目视对比，不代表实测或结构验证。', controls: '对比高度基准', model: '模型GL', official: '官方案内高度', source: '照片来源及拍摄条件（可选）', failed: '保存失败，请重试。' },
  en: { title: 'Compare a photo', file: 'Choose reference image', note: 'Images stay on this device and are never uploaded. Use front or side view, then align the image position and scale.', limit: 'PNG, JPEG or WebP, up to 12 MB.', invalid: 'Could not read the image. Choose PNG, JPEG or WebP up to 12 MB.', visible: 'Overlay reference image', opacity: 'Image opacity', scale: 'Image scale', x: 'Horizontal position', y: 'Vertical position', rotation: 'Image rotation', reset: 'Reset alignment', remove: 'Remove image', record: 'Save comparison settings', png: 'Save comparison image', caution: 'Photo perspective and lens differences are not corrected. This is a visual comparison, not a survey or structural verification.', controls: 'Height references', model: 'Model GL', official: 'Published guidance heights', source: 'Photo source and camera information (optional)', failed: 'Could not save. Please try again.' },
} as const;

function save(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob), link = document.createElement('a');
  link.href = url; link.download = name; document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 30_000);
}

export default function ReferenceCompare({ model, target, ready, camera, capture }: {
  model: LandmarkId; target: HTMLElement | null; ready: boolean; camera: LandmarkCamera; capture(): string | null;
}) {
  const { locale } = useLanguage(), copy = messages[locale], metadata = landmarkModels[model];
  const controlsId = useId();
  const [photo, setPhoto] = useState<{ url: string; name: string; sha256: string } | null>(null);
  const [alignment, setAlignment] = useState<ReferenceAlignment>(defaultReferenceAlignment);
  const [shown, setShown] = useState(true), [error, setError] = useState<'image' | 'save' | null>(null), [source, setSource] = useState('');
  const [imageReady, setImageReady] = useState(false);
  const [saving, setSaving] = useState(false);
  const image = useRef<HTMLImageElement | null>(null), request = useRef(0);
  useEffect(() => () => { request.current++; }, []);
  useEffect(() => () => { if (photo) URL.revokeObjectURL(photo.url); }, [photo]);
  async function select(file: File | undefined) {
    const current = ++request.current; setError(null);
    if (!file) return;
    if (!validReferenceImage(file)) { setError('image'); return; }
    try {
      const digest = await crypto.subtle.digest('SHA-256', await file.arrayBuffer());
      if (current !== request.current) return;
      setImageReady(false); setPhoto({ url: URL.createObjectURL(file), name: file.name, sha256: [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('') });
      setAlignment(defaultReferenceAlignment); setShown(true); setSource('');
    } catch { if (current === request.current) setError('image'); }
  }
  function record() {
    if (!imageReady || !photo) return;
    const canvas = target?.querySelector('canvas');
    let pose: unknown = null;
    try { pose = JSON.parse(canvas?.dataset.cameraPose ?? 'null'); } catch { /* No camera data before first render. */ }
    save(new Blob([JSON.stringify({ schema_version: 1, model, revision: metadata.revision,
      model_sha256: assetSha256(`GLB/${metadata.stem}.glb`), created_at: new Date().toISOString(),
      reference: { name: photo?.name, sha256: photo?.sha256, source, width: image.current?.naturalWidth, height: image.current?.naturalHeight },
      alignment, overlay_visible: shown, camera: { preset: camera, pose },
      viewport: { width: target?.clientWidth, height: target?.clientHeight, pixel_ratio: canvas && target?.clientWidth ? canvas.width / target.clientWidth : null,
        backing_width: canvas?.width, backing_height: canvas?.height, device_pixel_ratio: window.devicePixelRatio },
      controls: { height_mm: metadata.height, model_gl_levels_mm: metadata.levels, published_guidance_levels_mm: 'nominalLevels' in metadata ? metadata.nominalLevels : metadata.levels },
      status: 'manual_visual_comparison_unverified', perspective_calibrated: false,
    }, null, 2)], { type: 'application/json' }), `${metadata.stem}_comparison.json`);
  }
  async function snapshot() {
    const token = request.current;
    setSaving(true); setError(null);
    try {
      const bytes = capture(), reference = image.current;
      if (!bytes || !reference?.complete || !reference.naturalWidth || !target) throw new Error('Not ready.');
      const modelImage = new Image(); modelImage.src = bytes; await modelImage.decode();
      if (token !== request.current) return;
      const output = document.createElement('canvas'); output.width = modelImage.naturalWidth; output.height = modelImage.naturalHeight;
      const context = output.getContext('2d'); if (!context) throw new Error('Canvas unavailable.');
      context.drawImage(modelImage, 0, 0);
      if (shown) {
        const r = referenceImageRect(output.width, output.height, reference.naturalWidth, reference.naturalHeight, alignment);
        context.save(); context.globalAlpha = r.opacity; context.translate(r.centerX, r.centerY); context.rotate(r.rotation);
        context.drawImage(reference, -r.width / 2, -r.height / 2, r.width, r.height); context.restore();
      }
      const blob = await new Promise<Blob | null>(resolve => output.toBlob(resolve, 'image/png'));
      if (token !== request.current) return;
      if (!blob) throw new Error('Canvas encoding failed.');
      save(blob, `${metadata.stem}_comparison.png`);
    } catch { if (token === request.current) setError('save'); }
    finally { setSaving(false); }
  }
  return <section className="reference-compare" aria-label={copy.title}>
    <details><summary>{copy.title}</summary>
      <p>{copy.note}</p>
      <label className="reference-file">{copy.file}<input type="file" accept="image/png,image/jpeg,image/webp" onChange={event => { void select(event.target.files?.[0]); event.target.value = ''; }} /></label>
      <p>{copy.limit} ≤32 MP · ≤16384 px</p>
      {photo ? <>
        <p className="reference-photo-name">{photo.name}</p>
        <label className="reference-visible"><input type="checkbox" checked={shown} onChange={event => setShown(event.target.checked)} />{copy.visible}</label>
        {(Object.keys(defaultReferenceAlignment) as (keyof ReferenceAlignment)[]).map(key => <label key={key} htmlFor={`${controlsId}-${key}`} className="reference-range">{copy[key]}<output aria-hidden="true">{key === 'opacity' ? `${Math.round(alignment[key] * 100)}%` : alignment[key]}</output>
          <input id={`${controlsId}-${key}`} type="range" min={referenceLimits[key][0]} max={referenceLimits[key][1]} step={key === 'scale' || key === 'opacity' ? .01 : 1} value={alignment[key]}
            onChange={event => setAlignment(previous => referenceAlignment({ ...previous, [key]: Number(event.target.value) }))} /></label>)}
        <label className="reference-source">{copy.source}<input type="text" maxLength={1000} value={source} onChange={event => setSource(event.target.value)} /></label>
        <div className="reference-actions"><button className="outline-button" onClick={() => setAlignment(defaultReferenceAlignment)}>{copy.reset}</button><button className="outline-button" onClick={() => { request.current++; setPhoto(null); setImageReady(false); }}>{copy.remove}</button>
          <button className="outline-button" disabled={!ready || !imageReady} onClick={record}>{copy.record}</button><button className="outline-button" disabled={!ready || !imageReady || saving} onClick={() => void snapshot()}>{copy.png}</button></div>
      </> : null}
      <dl className="landmark-parameters" aria-label={copy.controls}><div><dt>{copy.model}</dt><dd>{metadata.levels.map(n => n / 1000).join(' / ')} m</dd></div>
        {'nominalLevels' in metadata ? <div><dt>{copy.official}</dt><dd>{metadata.nominalLevels.map(n => n / 1000).join(' / ')} m</dd></div> : null}</dl>
      <p>{copy.caution}</p>{error ? <p role="alert">{error === 'save' ? copy.failed : copy.invalid}</p> : null}
    </details>
    {target && photo ? createPortal(<div className="reference-image-overlay" hidden={!shown} aria-hidden="true"><img ref={image} src={photo.url} alt="" onLoad={event => {
      if (validReferenceDimensions(event.currentTarget.naturalWidth, event.currentTarget.naturalHeight)) setImageReady(true);
      else { request.current++; setPhoto(null); setImageReady(false); setError('image'); }
    }} onError={() => { request.current++; setPhoto(null); setImageReady(false); setError('image'); }} style={{ opacity: alignment.opacity, transform: referenceTransform(alignment) }} /></div>, target) : null}
  </section>;
}
