import { useModel } from './ModelContext';

export default function Parameters({ hideTitle = false }: { hideTitle?: boolean }) {
  const { copy, data } = useModel();
  return <section className="parameters">
    {!hideTitle ? <h2>{copy.parameters.title}</h2> : null}
    <dl>
      <div><dt>{copy.parameters.units}</dt><dd>{copy.parameters.millimetres}</dd></div>
      <div><dt>{copy.parameters.outline}</dt><dd>{data.parameters.width} × {data.parameters.depth}</dd></div>
      <div><dt>{copy.parameters.storey}</dt><dd>{data.parameters.storey_height}</dd></div>
      {data.parameters.clear_height !== undefined ? <div><dt>{copy.parameters.clearHeight}</dt><dd>{data.parameters.clear_height}</dd></div> : null}
      {data.areas ? <>
        <div><dt>{copy.parameters.outlineArea}</dt><dd>{data.areas.outline.toFixed(2)} m²</dd></div>
        <div><dt>{copy.parameters.interiorArea}</dt><dd>{data.areas.interior.toFixed(2)} m²</dd></div>
        <div><dt>{copy.parameters.balconyArea}</dt><dd>{data.areas.balcony.toFixed(2)} m²</dd></div>
      </> : null}
    </dl>
    <p className="muted-note">{copy.parameters.note}</p>
  </section>;
}
