import { house } from './data';

export default function Parameters() {
  return <section className="parameters">
    <h2>方案参数</h2>
    <dl>
      <div><dt>单位</dt><dd>毫米</dd></div>
      <div><dt>外轮廓</dt><dd>{house.parameters.width} × {house.parameters.depth}</dd></div>
      <div><dt>层高</dt><dd>{house.parameters.storey_height}</dd></div>
    </dl>
    <p className="muted-note">尺寸为演示假设。<br />结构与管线尚未建模。</p>
  </section>;
}
