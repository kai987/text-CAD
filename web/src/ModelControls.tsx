import type { Dispatch, SetStateAction } from 'react';
import { clampCutHeight } from './model-state';
import type { ModelPartId, ModelSettings } from './model-state';
import Parameters from './Parameters';
import PartTree from './PartTree';
import { useModel } from './ModelContext';
import StructuralOptions from './StructuralOptions';
import ControlSection from './ControlSection';
import { structuralCopy } from './structural-design';
import { useLanguage } from './LanguageContext';

interface Props {
  settings: ModelSettings;
  setSettings: Dispatch<SetStateAction<ModelSettings>>;
  ready: boolean;
  selectedPart?: ModelPartId | null;
  onSelectPart?: (id: ModelPartId, fit?: boolean) => void;
  structuralParts?: readonly ModelPartId[];
}
export default function ModelControls({ settings, setSettings, ready, selectedPart, onSelectPart, structuralParts }: Props) {
  const { copy, layout } = useModel();
  const { locale } = useLanguage();
  return <aside className="sidebar" aria-label={copy.controls.region}>
    <section>
      <h2>{copy.controls.cut}</h2>
      <label className="switch-control">
        <input type="checkbox" role="switch" aria-label={copy.controls.enableCut} checked={settings.cutaway} disabled={!ready}
          onChange={e => setSettings(s => ({ ...s, cutaway: e.target.checked }))} />
        <span className="switch-track" aria-hidden="true" />
      </label>
      <div className={settings.cutaway ? 'cut-controls' : 'cut-controls inactive'}>
        <label htmlFor="cut-height">{copy.controls.height}</label>
        <div className="range-row">
          <input id="cut-height" type="range" min="0" max={layout.maxCutHeight} step="100" value={settings.heightMm}
            disabled={!ready || !settings.cutaway}
            onChange={e => setSettings(s => ({ ...s, heightMm: clampCutHeight(Number(e.target.value), layout) }))} />
          <output htmlFor="cut-height">{settings.heightMm} mm</output>
        </div>
      </div>
    </section>
    <ControlSection title={copy.controls.parts} initiallyOpen={window.matchMedia('(min-width: 761px)').matches}>
      <PartTree settings={settings} setSettings={setSettings} ready={ready}
        selectedPart={selectedPart} onSelectPart={onSelectPart} structuralParts={structuralParts} />
    </ControlSection>
    {layout.id === 'house' ? <ControlSection title={structuralCopy.title[locale]}><StructuralOptions showSelectors={false} hideTitle /></ControlSection> : null}
    <ControlSection title={copy.parameters.title}><Parameters hideTitle /></ControlSection>
  </aside>;
}
