import { useEffect, useId, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { assetSha256 } from './data';
import { useLanguage } from './LanguageContext';
import { landmarkCameraOptions, landmarkModels } from './landmark-copy';
import type { LandmarkCamera, LandmarkId } from './landmark-copy';
import { defaultReferenceAlignment, referenceAlignment, referenceImageRect, referenceLimits, referenceTransform, validReferenceImage, validReferenceDimensions, referenceImagePoint, referenceImageCoordinate, referencePointError } from './reference-review';
import type { ReferenceAlignment } from './reference-review';
import { ComparisonRecordError, comparisonRecordLimit, parseComparisonRecord, restoreReferenceAnchors, validReferencePoint, validReferencePose } from './reference-record';
import type { ComparisonOrigin, ComparisonRecord, ReferenceAnchor, ReferenceCameraPose, ReferencePoint } from './reference-record';

const messages = {
  ja: { title: '写真と比較', file: '参考画像を選択', note: '画像は端末内で処理され、送信されません。正面・側面の視点から、位置と大きさを合わせて確認できます。', limit: 'PNG・JPEG・WebP、12 MBまで。', invalid: '画像を読み込めません。PNG・JPEG・WebP（12 MB以下）を選んでください。', visible: '画像を重ねる', opacity: '画像の不透明度', scale: '画像の倍率', x: '左右の位置', y: '上下の位置', rotation: '画像の回転', reset: '位置をリセット', remove: '画像を外す', record: '比較条件を保存', png: '比較画像を保存', caution: '写真の遠近感やレンズの差は補正していません。外観の目視比較用で、実測や構造の検証ではありません。', controls: '比較用の高さ基準', model: 'モデルGL', official: '公式案内高さ', source: '写真の出典・撮影条件（任意）', failed: '保存できませんでした。もう一度お試しください。' },
  zh: { title: '照片对比', file: '选择参考图片', note: '图片仅在本机处理，不会上传。可用正面或侧面视角调整位置与大小后对比。', limit: 'PNG、JPEG、WebP，最大12 MB。', invalid: '无法读取图片。请选择12 MB以内的PNG、JPEG或WebP。', visible: '叠加参考图片', opacity: '图片不透明度', scale: '图片缩放', x: '左右位置', y: '上下位置', rotation: '图片旋转', reset: '重置位置', remove: '移除图片', record: '保存对比条件', png: '保存对比图片', caution: '尚未校正照片透视与镜头差异。仅供外观目视对比，不代表实测或结构验证。', controls: '对比高度基准', model: '模型GL', official: '官方案内高度', source: '照片来源及拍摄条件（可选）', failed: '保存失败，请重试。' },
  en: { title: 'Compare a photo', file: 'Choose reference image', note: 'Images stay on this device and are never uploaded. Use front or side view, then align the image position and scale.', limit: 'PNG, JPEG or WebP, up to 12 MB.', invalid: 'Could not read the image. Choose PNG, JPEG or WebP up to 12 MB.', visible: 'Overlay reference image', opacity: 'Image opacity', scale: 'Image scale', x: 'Horizontal position', y: 'Vertical position', rotation: 'Image rotation', reset: 'Reset alignment', remove: 'Remove image', record: 'Save comparison settings', png: 'Save comparison image', caution: 'Photo perspective and lens differences are not corrected. This is a visual comparison, not a survey or structural verification.', controls: 'Height references', model: 'Model GL', official: 'Published guidance heights', source: 'Photo source and camera information (optional)', failed: 'Could not save. Please try again.' },
} as const;

const restorationMessages = {
  ja: {
    import: '比較条件を読み込む', imported: '写真の位置合わせとカメラを復元しました。', legacyRestored: '旧形式の条件を復元しました。保存時の画角情報がないため、現行プリセットの画角を使います。',
    recordError: '比較条件を読み込めません。128 KB以下の有効な比較JSONを選んでください。',
    modelError: '保存されたモデルIDが現在のモデルと一致しません。',
    revisionChange: '別の改訂で保存された比較条件です。写真とカメラ条件を適用し、モデル側の基準点を選び直せます。', savedRevision: '保存時の改訂', currentRevision: '現在の改訂', applyRevision: '現在のモデルに写真・カメラ条件を適用', adapted: '別改訂の写真・カメラ条件を適用しました。モデル側の基準点を選び直してください。', origin: '比較条件の元の改訂',
    photoError: '先に保存時と同じ写真を選んでください。写真のハッシュと画素寸法を照合します。',
    cameraError: 'カメラを復元できませんでした。モデルの読み込み後にお試しください。',
    anchors: '基準点の比較', photoPoint: '写真の点', modelPoint: 'モデルの点', addAnchor: '対応する基準点を追加', clearAnchors: '基準点を消す',
    pickReference: '写真上の基準点をクリックしてください。', pickModel: 'モデル上の対応点をクリックしてください。',
    cancelPick: '点の選択を終了', outside: '写真の内側を選んでください。',
    pointNote: '写真の点とモデルの点の画面上の差を、CSS pxと画面対角線に対する割合で表示します。',
    viewChanged: '視点または表示サイズが変わったため、基準点を解除しました。',
    removePoint: '基準点を削除', point: '点', keyboard: 'キーボードでは矢印キーで位置を動かし、Enterで点を確定します。',
  },
  zh: {
    import: '载入对比条件', imported: '已恢复照片、位置对齐和相机。', legacyRestored: '已恢复旧格式条件。旧记录没有保存画幅，使用当前预设画幅。',
    recordError: '无法载入对比条件。请选择128 KB以内的有效对比JSON。',
    modelError: '保存的模型ID与当前模型不一致。',
    revisionChange: '对比条件来自其他版本。可应用照片和相机条件，并重新选择模型基准点。', savedRevision: '保存版本', currentRevision: '当前版本', applyRevision: '将照片和相机条件应用到当前模型', adapted: '已应用其他版本的照片和相机条件。请重新选择模型基准点。', origin: '对比条件来源版本',
    photoError: '请先选择保存时的同一张照片。将核对照片哈希和像素尺寸。',
    cameraError: '无法恢复相机，请在模型加载后重试。',
    anchors: '基准点对比', photoPoint: '照片点', modelPoint: '模型点', addAnchor: '添加一组对应基准点', clearAnchors: '清除基准点',
    pickReference: '请点击照片上的基准点。', pickModel: '请点击模型上的对应点。',
    cancelPick: '结束选点', outside: '请在照片范围内选点。',
    pointNote: '照片点与模型点的屏幕偏差以CSS px和屏幕对角线百分比显示。',
    viewChanged: '视角或显示尺寸已变化，基准点已清除。',
    removePoint: '删除基准点', point: '点', keyboard: '可用方向键移动选点位置，按Enter确认。',
  },
  en: {
    import: 'Load comparison settings', imported: 'Restored the photo alignment and camera.', legacyRestored: 'Restored legacy settings using the current preset framing because the record has no saved camera span.',
    recordError: 'Could not load settings. Choose a valid comparison JSON file up to 128 KB.',
    modelError: 'The saved model ID does not match the current model.',
    revisionChange: 'These conditions were saved for another revision. Apply its photo and camera conditions, then select fresh model points.', savedRevision: 'Saved revision', currentRevision: 'Current revision', applyRevision: 'Apply photo and camera conditions to this model', adapted: 'Applied conditions from another revision. Select fresh model points.', origin: 'Comparison conditions from revision',
    photoError: 'Choose the same photo first. Its hash and pixel dimensions must match the saved record.',
    cameraError: 'Could not restore the camera. Try again after the model loads.',
    anchors: 'Reference points', photoPoint: 'Photo point', modelPoint: 'Model point', addAnchor: 'Add matching reference points', clearAnchors: 'Clear reference points',
    pickReference: 'Click a reference point on the photo.', pickModel: 'Click the matching point on the model.',
    cancelPick: 'Finish selecting points', outside: 'Choose a point inside the photo.',
    pointNote: 'Image-space differences are shown in CSS pixels and as a percentage of the viewport diagonal.',
    viewChanged: 'The view or viewport changed, so the reference points were cleared.',
    removePoint: 'Remove reference point', point: 'Point', keyboard: 'Use arrow keys to move the marker and Enter to confirm a point.',
  },
} as const;

function save(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob), link = document.createElement('a');
  link.href = url; link.download = name; document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 30_000);
}
interface ReferencePhoto { url: string; name: string; sha256: string; width: number; height: number }
type PointSelection = { stage: 'reference' } | { stage: 'model'; reference: ReferencePoint };
type ComparisonError = 'image' | 'save' | 'record' | 'model' | 'photo' | 'camera' | 'outside';

export default function ReferenceCompare({ model, target, ready, camera, capture, restoreCamera, onPickingChange }: {
  model: LandmarkId; target: HTMLElement | null; ready: boolean; camera: LandmarkCamera; capture(): string | null;
  restoreCamera(preset: LandmarkCamera, pose: ReferenceCameraPose): boolean;
  onPickingChange(picking: boolean): void;
}) {
  const { locale } = useLanguage(), copy = { ...messages[locale], ...restorationMessages[locale] }, metadata = landmarkModels[model];
  const controlsId = useId();
  const [photo, setPhoto] = useState<ReferencePhoto | null>(null);
  const [alignment, setAlignment] = useState<ReferenceAlignment>(defaultReferenceAlignment);
  const [shown, setShown] = useState(true), [error, setError] = useState<ComparisonError | null>(null), [source, setSource] = useState('');
  const [imageReady, setImageReady] = useState(false), [saving, setSaving] = useState(false);
  const [anchors, setAnchors] = useState<ReferenceAnchor[]>([]);
  const [pendingRecord, setPendingRecord] = useState<ComparisonRecord | null>(null);
  const [origin, setOrigin] = useState<ComparisonOrigin | null>(null);
  const [picking, setPicking] = useState<PointSelection | null>(null);
  const [cursor, setCursor] = useState<ReferencePoint>({ x: .5, y: .5 });
  const [notice, setNotice] = useState<'restored' | 'legacy' | 'view' | 'adapted' | null>(null);
  const image = useRef<HTMLImageElement | null>(null), request = useRef(0);
  const anchorsRef = useRef(anchors); anchorsRef.current = anchors;
  const pickingRef = useRef(picking); pickingRef.current = picking;
  useEffect(() => () => { request.current++; }, []);
  useEffect(() => () => { if (photo) URL.revokeObjectURL(photo.url); }, [photo]);
  useEffect(() => { onPickingChange(!!picking); return () => onPickingChange(false); }, [picking, onPickingChange]);
  useEffect(() => {
    if (!ready) setPendingRecord(null);
    if (!ready && (anchorsRef.current.length || pickingRef.current)) {
      setAnchors([]); setPicking(null); setNotice('view');
    }
  }, [ready]);
  useEffect(() => {
    const changed = () => {
      if (anchorsRef.current.length || pickingRef.current) { setAnchors([]); setPicking(null); setNotice('view'); }
    };
    target?.addEventListener('comparisoncamerachange', changed);
    return () => target?.removeEventListener('comparisoncamerachange', changed);
  }, [target]);

  async function select(file: File | undefined) {
    if (!file) return;
    const current = ++request.current; setError(null); setNotice(null); setPicking(null); setPendingRecord(null);
    if (!validReferenceImage(file)) { setError('image'); return; }
    let url: string | null = null;
    try {
      const digest = await crypto.subtle.digest('SHA-256', await file.arrayBuffer());
      if (current !== request.current) return;
      url = URL.createObjectURL(file);
      const decoded = new Image(); decoded.src = url; await decoded.decode();
      if (current !== request.current) { URL.revokeObjectURL(url); return; }
      if (!validReferenceDimensions(decoded.naturalWidth, decoded.naturalHeight)) throw new Error('Invalid image dimensions.');
      setImageReady(false); setPhoto({ url, name: file.name, sha256: [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join(''), width: decoded.naturalWidth, height: decoded.naturalHeight });
      setAlignment(defaultReferenceAlignment); setShown(true); setSource(''); setAnchors([]); setOrigin(null);
    } catch {
      if (url) URL.revokeObjectURL(url);
      if (current === request.current) setError('image');
    }
  }
  async function importRecord(file: File | undefined) {
    if (!file) return;
    const token = ++request.current; setError(null); setNotice(null); setPicking(null); setPendingRecord(null);
    if (!ready || !imageReady || !photo || !target) { setError('photo'); return; }
    if (!file.size || file.size > comparisonRecordLimit) { setError('record'); return; }
    try {
      const text = await file.text();
      if (token !== request.current) return;
      const identity = {
        model, revision: metadata.revision, modelSha256: assetSha256(`GLB/${metadata.stem}.glb`) ?? '',
        photoSha256: photo.sha256, width: photo.width, height: photo.height,
        cameras: [...landmarkCameraOptions(model), ...(model === 'tokyo-tower' ? ['steel-node'] : [])],
      };
      let record: ComparisonRecord;
      try { record = parseComparisonRecord(text, identity); }
      catch (failure) {
        if (failure instanceof ComparisonRecordError && failure.reason === 'revision') {
          setPendingRecord(parseComparisonRecord(text, identity, { allowRevisionChange: true })); return;
        }
        throw failure;
      }
      applyRecord(record, false);
    } catch (failure) {
      if (token === request.current) setError(failure instanceof ComparisonRecordError && failure.reason !== 'revision' ? failure.reason : 'record');
    }
  }
  function applyRecord(record: ComparisonRecord, revisionChanged: boolean) {
    if (!ready || !imageReady || !photo || !target || record.reference.sha256 !== photo.sha256
      || record.reference.width !== photo.width || record.reference.height !== photo.height) { setError('photo'); return; }
    if (!restoreCamera(record.camera.preset as LandmarkCamera, record.camera.pose)) { setError('camera'); return; }
    setAlignment(record.alignment); setShown(record.overlay_visible); setSource(record.source);
    setAnchors(revisionChanged ? [] : restoreReferenceAnchors(record.anchor_points, record.viewport, { width: target.clientWidth, height: target.clientHeight }));
    setOrigin(revisionChanged ? { revision: record.revision, model_sha256: record.model_sha256 } : record.comparison_origin ?? null);
    setPendingRecord(null); setError(null);
    setNotice(record.camera.pose.verticalSpan === undefined ? 'legacy' : revisionChanged ? 'adapted' : 'restored');
  }

  function record() {
    if (!imageReady || !photo || !target) return;
    try {
      const canvas = target.querySelector('canvas');
      const pose: unknown = JSON.parse(canvas?.dataset.cameraPose ?? 'null');
      if (!validReferencePose(pose)) throw new Error('Camera not ready.');
      save(new Blob([JSON.stringify({ schema_version: 2, model, revision: metadata.revision,
        model_sha256: assetSha256(`GLB/${metadata.stem}.glb`), created_at: new Date().toISOString(),
        reference: { name: photo.name, sha256: photo.sha256, source, width: photo.width, height: photo.height },
        alignment, overlay_visible: shown, camera: { preset: camera, pose }, anchor_points: anchors,
        ...(origin ? { comparison_origin: origin } : {}),
        viewport: { width: target.clientWidth, height: target.clientHeight, pixel_ratio: canvas ? canvas.width / target.clientWidth : null,
          backing_width: canvas?.width, backing_height: canvas?.height, device_pixel_ratio: window.devicePixelRatio },
        controls: { height_mm: metadata.height, model_gl_levels_mm: metadata.levels, published_guidance_levels_mm: 'nominalLevels' in metadata ? metadata.nominalLevels : metadata.levels },
        status: 'manual_visual_comparison_unverified', perspective_calibrated: false,
      }, null, 2)], { type: 'application/json' }), `${metadata.stem}_comparison.json`);
    } catch { setError('save'); }
  }
  function pointPositions(width: number, height: number) {
    if (!photo) return [];
    return anchors.map(anchor => ({
      reference: referenceImagePoint(width, height, photo.width, photo.height, alignment, anchor.reference),
      model: { x: anchor.model.x * width, y: anchor.model.y * height },
      error: referencePointError(referenceImagePoint(width, height, photo.width, photo.height, alignment, anchor.reference), anchor.model, width, height),
    }));
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
        const scale = output.width / target.clientWidth;
        context.lineWidth = 2 * scale; context.font = `${13 * scale}px sans-serif`;
        pointPositions(output.width, output.height).forEach((pair, index) => {
          context.strokeStyle = '#ffd800'; context.beginPath(); context.moveTo(pair.reference.x, pair.reference.y); context.lineTo(pair.model.x, pair.model.y); context.stroke();
          for (const [point, color] of [[pair.reference, '#00bcd4'], [pair.model, '#db2777']] as const) {
            context.fillStyle = color; context.beginPath(); context.arc(point.x, point.y, 5 * scale, 0, Math.PI * 2); context.fill();
            context.fillText(String(index + 1), point.x + 8 * scale, point.y - 8 * scale);
          }
        });
      }
      const blob = await new Promise<Blob | null>(resolve => output.toBlob(resolve, 'image/png'));
      if (token !== request.current) return;
      if (!blob) throw new Error('Canvas encoding failed.');
      save(blob, `${metadata.stem}_comparison.png`);
    } catch { if (token === request.current) setError('save'); }
    finally { setSaving(false); }
  }
  function selectPoint(point: ReferencePoint) {
    if (!photo || !target || !picking) return;
    setError(null);
    if (picking.stage === 'reference') {
      const selected = referenceImageCoordinate(target.clientWidth, target.clientHeight, photo.width, photo.height, alignment,
        { x: point.x * target.clientWidth, y: point.y * target.clientHeight });
      if (!validReferencePoint(selected)) { setError('outside'); return; }
      setPicking({ stage: 'model', reference: selected });
    } else {
      setAnchors(previous => [...previous, { reference: picking.reference, model: point }]); setPicking(null); setNotice(null);
    }
  }
  const positions = pointPositions(target?.clientWidth ?? 1, target?.clientHeight ?? 1);
  const errorText = error === 'image' ? copy.invalid : error === 'save' ? copy.failed : error === 'record' ? copy.recordError
    : error === 'model' ? copy.modelError : error === 'photo' ? copy.photoError : error === 'camera' ? copy.cameraError : copy.outside;
  return <section className="reference-compare" aria-label={copy.title}>
    <details><summary>{copy.title}</summary>
      <p>{copy.note}</p>
      <label className="reference-file">{copy.file}<input type="file" accept="image/png,image/jpeg,image/webp" onChange={event => { void select(event.target.files?.[0]); event.target.value = ''; }} /></label>
      <p>{copy.limit} ≤32 MP · ≤16384 px</p>
      <label className="reference-file">{copy.import}<input type="file" accept="application/json,.json" disabled={!ready || !imageReady} onChange={event => { void importRecord(event.target.files?.[0]); event.target.value = ''; }} /></label>
      {pendingRecord ? <div className="reference-revision-confirm" role="status"><p>{copy.revisionChange}</p>
        <p>{copy.savedRevision} {pendingRecord.revision} · {pendingRecord.model_sha256.slice(0, 8)}<br />{copy.currentRevision} {metadata.revision} · {assetSha256(`GLB/${metadata.stem}.glb`)?.slice(0, 8)}</p>
        <button className="outline-button" disabled={!ready || !imageReady} onClick={() => applyRecord(pendingRecord, true)}>{copy.applyRevision}</button>
      </div> : null}
      {photo ? <>
        <p className="reference-photo-name">{photo.name}</p>
        {origin ? <p>{copy.origin} {origin.revision}</p> : null}
        <label className="reference-visible"><input type="checkbox" checked={shown} onChange={event => setShown(event.target.checked)} />{copy.visible}</label>
        {(Object.keys(defaultReferenceAlignment) as (keyof ReferenceAlignment)[]).map(key => <label key={key} htmlFor={`${controlsId}-${key}`} className="reference-range">{copy[key]}<output aria-hidden="true">{key === 'opacity' ? `${Math.round(alignment[key] * 100)}%` : alignment[key]}</output>
          <input id={`${controlsId}-${key}`} type="range" min={referenceLimits[key][0]} max={referenceLimits[key][1]} step={key === 'scale' || key === 'opacity' ? .01 : 1} value={alignment[key]}
            onChange={event => setAlignment(previous => referenceAlignment({ ...previous, [key]: Number(event.target.value) }))} /></label>)}
        <label className="reference-source">{copy.source}<input type="text" maxLength={1000} value={source} onChange={event => setSource(event.target.value)} /></label>
        <div className="reference-actions"><button className="outline-button" onClick={() => setAlignment(defaultReferenceAlignment)}>{copy.reset}</button><button className="outline-button" onClick={() => { request.current++; setPhoto(null); setImageReady(false); setAnchors([]); setPicking(null); setNotice(null); setOrigin(null); setPendingRecord(null); }}>{copy.remove}</button>
          <button className="outline-button" disabled={!ready || !imageReady || !!picking} onClick={record}>{copy.record}</button><button className="outline-button" disabled={!ready || !imageReady || saving || !!picking} onClick={() => void snapshot()}>{copy.png}</button></div>
        <div className="reference-points"><h3>{copy.anchors}</h3><p>{copy.pointNote}</p>
          <p className="reference-point-legend"><span className="reference-photo-legend">{copy.photoPoint}</span><span className="reference-model-legend">{copy.modelPoint}</span></p>
          <button className="outline-button" disabled={!ready || !imageReady || anchors.length >= 16 || !!picking} onClick={() => { setShown(true); setPicking({ stage: 'reference' }); setCursor({ x: .5, y: .5 }); setError(null); }}>{copy.addAnchor}</button>
          {picking ? <><p role="status">{picking.stage === 'reference' ? copy.pickReference : copy.pickModel}</p><p>{copy.keyboard}</p><button className="outline-button" onClick={() => setPicking(null)}>{copy.cancelPick}</button></> : null}
          {positions.length ? <><ol>{positions.map((pair, index) => <li key={index}>
            <span>{copy.point} {index + 1} <output>{pair.error.pixels.toFixed(1)} px · {pair.error.diagonalPercent.toFixed(2)}%</output></span>
            <button className="outline-button" aria-label={`${copy.removePoint} ${index + 1}`} onClick={() => setAnchors(previous => previous.filter((_, i) => i !== index))}>×</button>
          </li>)}</ol><button className="outline-button" onClick={() => setAnchors([])}>{copy.clearAnchors}</button></> : null}
        </div>
      </> : null}
      <dl className="landmark-parameters" aria-label={copy.controls}><div><dt>{copy.model}</dt><dd>{metadata.levels.map(n => n / 1000).join(' / ')} m</dd></div>
        {'nominalLevels' in metadata ? <div><dt>{copy.official}</dt><dd>{metadata.nominalLevels.map(n => n / 1000).join(' / ') } m</dd></div> : null}</dl>
      <p>{copy.caution}</p>{notice ? <p role="status">{notice === 'restored' ? copy.imported : notice === 'legacy' ? copy.legacyRestored : notice === 'adapted' ? copy.adapted : copy.viewChanged}</p> : null}
      {error ? <p role="alert">{errorText}</p> : null}
    </details>
    {target && photo ? createPortal(<>
      <div className="reference-image-overlay" hidden={!shown || picking?.stage === 'model'} aria-hidden="true"><img ref={image} src={photo.url} alt="" onLoad={() => setImageReady(true)} onError={() => { request.current++; setPhoto(null); setImageReady(false); setAnchors([]); setPicking(null); setPendingRecord(null); setOrigin(null); setError('image'); }} style={{ opacity: alignment.opacity, transform: referenceTransform(alignment) }} /></div>
      {positions.length ? <svg className="reference-point-overlay" style={{ display: !shown || picking ? 'none' : undefined }} viewBox={`0 0 ${target.clientWidth} ${target.clientHeight}`} aria-hidden="true" data-anchor-count={positions.length}>
        {positions.map((pair, index) => <g key={index}>
          <line x1={pair.reference.x} y1={pair.reference.y} x2={pair.model.x} y2={pair.model.y} />
          <circle className="reference-photo-point" cx={pair.reference.x} cy={pair.reference.y} r="5" /><circle className="reference-model-point" cx={pair.model.x} cy={pair.model.y} r="5" />
          <text x={pair.reference.x + 8} y={pair.reference.y - 8}>{index + 1}</text>
        </g>)}
      </svg> : null}
      {picking ? <button className="reference-point-picker" aria-label={picking.stage === 'reference' ? copy.pickReference : copy.pickModel} autoFocus
        onClick={event => {
          if (event.detail === 0) { selectPoint(cursor); return; }
          const rect = event.currentTarget.getBoundingClientRect();
          selectPoint({ x: (event.clientX - rect.left) / rect.width, y: (event.clientY - rect.top) / rect.height });
        }} onKeyDown={event => {
          const deltas: Record<string, [number, number]> = { ArrowLeft: [-.01, 0], ArrowRight: [.01, 0], ArrowUp: [0, -.01], ArrowDown: [0, .01] };
          const delta = deltas[event.key];
          if (delta) { event.preventDefault(); setCursor(previous => ({ x: Math.max(0, Math.min(1, previous.x + delta[0])), y: Math.max(0, Math.min(1, previous.y + delta[1])) })); }
          if (event.key === 'Escape') { event.preventDefault(); setPicking(null); }
        }}><span className="reference-picker-cursor" style={{ left: `${cursor.x * 100}%`, top: `${cursor.y * 100}%` }}>+</span></button> : null}
    </>, target) : null}
  </section>;
}
