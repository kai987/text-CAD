import { house } from './data';
import { useLanguage } from './LanguageContext';

export default function Parameters() {
  const { copy } = useLanguage();
  return <section className="parameters">
    <h2>{copy.parameters.title}</h2>
    <dl>
      <div><dt>{copy.parameters.units}</dt><dd>{copy.parameters.millimetres}</dd></div>
      <div><dt>{copy.parameters.outline}</dt><dd>{house.parameters.width} × {house.parameters.depth}</dd></div>
      <div><dt>{copy.parameters.storey}</dt><dd>{house.parameters.storey_height}</dd></div>
    </dl>
    <p className="muted-note">{copy.parameters.note}</p>
  </section>;
}
