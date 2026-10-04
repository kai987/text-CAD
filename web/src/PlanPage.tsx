import { useState } from 'react';
import { Download, Minus, Plus, Scan } from 'lucide-react';
import { asset, house } from './data';
import Parameters from './Parameters';

export default function PlanPage({ floor }: { floor: 1 | 2 }) {
  const [zoom, setZoom] = useState(1);
  const [failed, setFailed] = useState(false);
  const rooms = house.floors.find(f => f.floor === floor)!.rooms;
  const dxf = floor === 1 ? '001D0PL2-1FPLAN.DXF' : '002D0PL2-2FPLAN.DXF';
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
        <div className="toolbar-actions plan-actions">
          <button type="button" className="outline-button icon-button" aria-label="缩小平面图" disabled={zoom <= 0.5} onClick={() => setZoom(z => Math.max(0.5, z - 0.25))}><Minus size={16} /></button>
          <output className="zoom-value" aria-label="平面图缩放比例">{Math.round(zoom * 100)}%</output>
          <button type="button" className="outline-button icon-button" aria-label="放大平面图" disabled={zoom >= 4} onClick={() => setZoom(z => Math.min(4, z + 0.25))}><Plus size={16} /></button>
          <button type="button" className="outline-button fit-button" onClick={() => setZoom(1)}><Scan size={16} />适合页面</button>
        </div>
      </div>
      <div className="plan-scroll">
        {failed ? <p role="alert">图纸预览无法加载，请下载 DXF 或打开 PDF。</p> :
          <img className="plan-sheet" style={{ width: `${zoom * 100}%` }}
            src={asset(`output/review/jp_floor_plan-${floor}.png`)} onError={() => setFailed(true)}
            alt={`${floor}层 A3 平面图，包含房间名、净尺寸、面积、图框和表题栏`} />}
      </div>
    </section>
  </div>;
}
