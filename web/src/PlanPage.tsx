import { useEffect, useRef, useState } from 'react';
import { Download, Minus, Plus, Scan } from 'lucide-react';
import { asset, house } from './data';
import Parameters from './Parameters';
import { fittedPlanWidth, planPreviews, planViewBox } from './plan-preview';
import type { PlanView } from './plan-preview';

// The approved PDF conversion is static; retain parsed vectors when switching floors.
const svgCache = new Map<string, Promise<string>>();
function loadPlanVectors(path: string) {
  let pending = svgCache.get(path);
  if (!pending) {
    pending = fetch(asset(path)).then(async response => {
      if (!response.ok) throw new Error('The vector plan could not be loaded.');
      const document = new DOMParser().parseFromString(await response.text(), 'image/svg+xml');
      if (document.querySelector('parsererror') || document.documentElement.localName !== 'svg' ||
          document.querySelector('script, foreignObject, image, text')) {
        throw new Error('Invalid vector plan.');
      }
      return document.documentElement.innerHTML;
    });
    svgCache.set(path, pending);
    pending.catch(() => svgCache.delete(path));
  }
  return pending;
}

export default function PlanPage({ floor }: { floor: 1 | 2 }) {
  const [zoom, setZoom] = useState(1);
  const [view, setView] = useState<PlanView>('plan');
  const [vectors, setVectors] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const [available, setAvailable] = useState({ width: 1, height: 1 });
  const scroll = useRef<HTMLDivElement>(null);
  const rooms = house.floors.find(f => f.floor === floor)!.rooms;
  const dxf = floor === 1 ? '001D0PL2-1FPLAN.DXF' : '002D0PL2-2FPLAN.DXF';
  const preview = planPreviews.find(item => item.floor === floor)!;
  const viewBox = planViewBox(floor, view);
  const width = fittedPlanWidth(viewBox, available.width, available.height) * zoom;

  useEffect(() => {
    let current = true;
    loadPlanVectors(preview.path).then(markup => {
      if (current) setVectors(markup);
    }).catch(() => { if (current) setFailed(true); });
    return () => { current = false; };
  }, [preview.path]);

  useEffect(() => {
    const element = scroll.current!;
    const measure = () => {
      const style = getComputedStyle(element);
      setAvailable({
        // Reserve the sheet's one-pixel border so 100% fit does not introduce scrollbars.
        width: Math.max(1, element.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight) - 2),
        height: Math.max(1, element.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom) - 2),
      });
    };
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    measure();
    return () => observer.disconnect();
  }, []);

  function fitPage() {
    setZoom(1);
    scroll.current?.scrollTo({ left: 0, top: 0 });
  }
  function changeView(next: PlanView) {
    setView(next);
    fitPage();
  }

  return <div className="workspace plan-workspace">
    <aside className="sidebar plan-sidebar" aria-label={`${floor}层图纸资料`}>
      <section><h2>{floor === 1 ? '一层平面' : '二层平面'}</h2>
        <p className="drawing-details">A3 横向 · 1:50 · 单位 mm</p>
        <a className="outline-button download-action" href={asset(`DXF/${dxf}`)} download><Download size={16} />下载 DXF</a>
        <a className="text-link" href={asset('output/pdf/house_floor_plans_R02_JP.pdf')} target="_blank" rel="noreferrer">打开两层 PDF 图纸</a>
      </section>
      <section><h2>房间净面积</h2>
        <table className="room-table"><thead><tr><th scope="col">房间</th><th scope="col">m²</th></tr></thead>
          <tbody>{rooms.map(r => <tr key={r.id}><th scope="row">{r.name}</th><td>{r.area.toFixed(2)}</td></tr>)}</tbody></table>
        <p className="muted-note">墙内净面积，含家具占地。楼梯项为梯间预留面积。</p>
      </section>
      <Parameters />
    </aside>
    <section className="viewer-panel" aria-label={`${floor}层平面图查看区域`}>
      <div className="viewer-toolbar"><h1>{floor === 1 ? '一层平面图' : '二层平面图'}</h1>
        <div className="plan-toolbar-controls">
          <div className="plan-view-switch" role="group" aria-label="图纸显示范围">
            <button type="button" aria-pressed={view === 'plan'} onClick={() => changeView('plan')}>只看平面</button>
            <button type="button" aria-pressed={view === 'sheet'} onClick={() => changeView('sheet')}>完整图框</button>
          </div>
        <div className="toolbar-actions plan-actions">
          <button type="button" className="outline-button icon-button" aria-label="缩小平面图" disabled={zoom <= 0.5} onClick={() => setZoom(z => Math.max(0.5, z - 0.25))}><Minus size={16} /></button>
          <output className="zoom-value" aria-label="平面图缩放比例">{Math.round(zoom * 100)}%</output>
          <button type="button" className="outline-button icon-button" aria-label="放大平面图" disabled={zoom >= 4} onClick={() => setZoom(z => Math.min(4, z + 0.25))}><Plus size={16} /></button>
          <button type="button" className="outline-button fit-button" onClick={fitPage}><Scan size={16} />适合页面</button>
        </div>
        </div>
      </div>
      <div className="plan-scroll" ref={scroll}>
        {failed ? <p role="alert">矢量图纸预览无法加载，请下载 DXF 或打开 PDF。</p> : vectors ?
          <svg className="plan-sheet plan-vector" xmlns="http://www.w3.org/2000/svg"
            viewBox={viewBox.join(' ')} width={width} height={width * viewBox[3] / viewBox[2]}
            style={{ width: `${width}px`, marginInline: width <= available.width ? 'auto' : 0 }}
            role="img" aria-label={`${floor}层${view === 'plan' ? '平面图' : '完整 A3 图纸'}，矢量预览；包含房间名、净尺寸、面积、门号和两向7280毫米外轮廓尺寸。${view === 'sheet' ? '包括图框、表题栏、面积表和假设说明。' : '可切换完整图框查看面积表和假设说明。'}`}
            dangerouslySetInnerHTML={{ __html: vectors }} /> :
          <p className="plan-preview-note" role="status">正在加载矢量图纸…</p>}
      </div>
    </section>
  </div>;
}
