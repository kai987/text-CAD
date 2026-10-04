import type { Dispatch, SetStateAction } from 'react';
import { clampCutHeight } from './model-state';
import type { ModelPartId, ModelSettings } from './model-state';
import Parameters from './Parameters';
import PartTree from './PartTree';
import { useLanguage } from './LanguageContext';

interface Props {
  settings: ModelSettings;
  setSettings: Dispatch<SetStateAction<ModelSettings>>;
  ready: boolean;
  selectedPart?: ModelPartId | null;
  onSelectPart?: (id: ModelPartId, fit?: boolean) => void;
}
export default function ModelControls({ settings, setSettings, ready, selectedPart, onSelectPart }: Props) {
  const { copy } = useLanguage();
  return <aside className="sidebar" aria-label={copy.controls.region}>
    <section>
      <h2>{copy.controls.parts}</h2>
      <PartTree settings={settings} setSettings={setSettings} ready={ready}
        selectedPart={selectedPart} onSelectPart={onSelectPart} />
    </section>
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
          <input id="cut-height" type="range" min="0" max="8000" step="100" value={settings.heightMm}
            disabled={!ready || !settings.cutaway}
            onChange={e => setSettings(s => ({ ...s, heightMm: clampCutHeight(Number(e.target.value)) }))} />
          <output htmlFor="cut-height">{settings.heightMm} mm</output>
        </div>
      </div>
    </section>
    <Parameters />
  </aside>;
}
