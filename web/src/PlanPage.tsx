import { useEffect, useRef, useState } from 'react';
import { Download, Minus, Plus, Scan } from 'lucide-react';
import { asset } from './data';
import Parameters from './Parameters';
import { fittedPlanWidth } from './plan-preview';
import type { PlanView } from './plan-preview';
import { useModel } from './ModelContext';
import { format, roomLabel } from './localization';
import { getCachedPlanVectors, loadPlanVectors } from './plan-vectors';

export default function PlanPage({ floor }: { floor: 1 | 2 }) {
  const { copy, data, previews, plans, pdf } = useModel();
  const preview = previews.find(item => item.floor === floor)!;
  const [zoom, setZoom] = useState(1);
  const [view, setView] = useState<PlanView>('plan');
  const [vectors, setVectors] = useState<string | null>(() => getCachedPlanVectors(preview.path) ?? null);
  const [failed, setFailed] = useState(false);
  const [available, setAvailable] = useState({ width: 1, height: 1 });
  const scroll = useRef<HTMLDivElement>(null);
  const rooms = data.floors.find(f => f.floor === floor)!.rooms;
  const dxf = plans[floor]!;
  const viewBox = view === 'plan' ? preview.planViewBox : preview.fullViewBox;
  const width = fittedPlanWidth(viewBox, available.width, available.height) * zoom;

  useEffect(() => {
    let current = true;
    setFailed(false);
    setVectors(getCachedPlanVectors(preview.path) ?? null);
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
    <aside className="sidebar plan-sidebar" aria-label={format(copy.plan.sidebar, { floor })}>
      <section><h2>{copy.app.tabs[floor === 1 ? '1f' : '2f']}</h2>
        <p className="drawing-details">{copy.plan.details}</p>
        <a className="outline-button download-action" href={asset(dxf)} download><Download size={16} />{copy.plan.downloadDxf}</a>
        <a className="text-link" href={asset(pdf)} target="_blank" rel="noreferrer">{copy.plan.openPdf}</a>
        <p className="muted-note">{copy.plan.originalNote}</p>
      </section>
      <section><h2>{copy.plan.areaTitle}</h2>
        <table className="room-table"><thead><tr><th scope="col">{copy.plan.room}</th><th scope="col">m²</th></tr></thead>
          <tbody>{rooms.map(r => <tr key={r.id}><th scope="row">{roomLabel(copy, r.id)}</th><td>{r.area.toFixed(2)}</td></tr>)}</tbody></table>
        <p className="muted-note">{copy.plan.areaNote}</p>
      </section>
      <Parameters />
    </aside>
    <section className="viewer-panel" aria-label={format(copy.plan.viewer, { floor })}>
      <div className="viewer-toolbar"><h1>{format(copy.plan.title, { floor })}</h1>
        <div className="plan-toolbar-controls">
          <div className="plan-view-switch" role="group" aria-label={copy.plan.range}>
            <button type="button" aria-pressed={view === 'plan'} onClick={() => changeView('plan')}>{copy.plan.planOnly}</button>
            <button type="button" aria-pressed={view === 'sheet'} onClick={() => changeView('sheet')}>{copy.plan.fullSheet}</button>
          </div>
        <div className="toolbar-actions plan-actions">
          <button type="button" className="outline-button icon-button" aria-label={copy.plan.zoomOut} disabled={zoom <= 0.5} onClick={() => setZoom(z => Math.max(0.5, z - 0.25))}><Minus size={16} /></button>
          <output className="zoom-value" aria-label={copy.plan.zoom}>{Math.round(zoom * 100)}%</output>
          <button type="button" className="outline-button icon-button" aria-label={copy.plan.zoomIn} disabled={zoom >= 4} onClick={() => setZoom(z => Math.min(4, z + 0.25))}><Plus size={16} /></button>
          <button type="button" className="outline-button fit-button" onClick={fitPage}><Scan size={16} />{copy.plan.fit}</button>
        </div>
        </div>
      </div>
      <div className="plan-scroll" ref={scroll}>
        {failed ? <p role="alert">{copy.plan.error}</p> : vectors ?
          <svg className="plan-sheet plan-vector" xmlns="http://www.w3.org/2000/svg"
            viewBox={viewBox.join(' ')} width={width} height={width * viewBox[3] / viewBox[2]}
            style={{ width: `${width}px`, marginInline: width <= available.width ? 'auto' : 0 }}
            role="img" aria-label={format(view === 'plan' ? copy.plan.previewPlan : copy.plan.previewSheet, { floor })}
            dangerouslySetInnerHTML={{ __html: vectors }} /> :
          <p className="plan-preview-note" role="status">{copy.plan.loading}</p>}
      </div>
    </section>
  </div>;
}
