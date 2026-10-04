import { ArrowUpRight, Download } from 'lucide-react';
import { asset, downloadFiles, house, repository } from './data';

export default function DownloadPage() {
  return <div className="downloads-page">
    <header><h1>文件下载</h1><p>当前图纸 {house.drawingRevision} · 三维模型 {house.modelRevision}</p></header>
    <div className="download-list">
      {downloadFiles.map(f => <a className="download-row" key={f.path} href={asset(f.path)} download>
        <span className="file-type">{f.type}</span><span className="file-description"><strong>{f.title}</strong><span>{f.detail}</span></span>
        <Download size={20} aria-hidden="true" /><span className="sr-only">下载</span>
      </a>)}
    </div>
    <a className="outline-button source-button" href={repository} target="_blank" rel="noreferrer">参数化 Python 源码<ArrowUpRight size={17} aria-hidden="true" /></a>
    <section className="assumptions"><h2>方案说明</h2>
      <p>7280 × 7280 mm 外轮廓及 2800 mm 层高是演示假设。当前模型用于方案查看，结构、墙体层次、设备管线及实际楼梯净空尚待深化。</p>
      <p>平面图采用東京都建設局 CAD 製图基准的共通项目用于住宅方案，保留可编辑标注；本次输出包含 DXF、STEP、GLB、PDF，未包含 SXF 电子纳品。</p>
    </section>
  </div>;
}
