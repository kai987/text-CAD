import type { Dispatch, SetStateAction } from 'react';
import { clampCutHeight } from './model-state';
import type { ModelPartId, ModelSettings } from './model-state';
import Parameters from './Parameters';
import PartTree from './PartTree';

interface Props {
  settings: ModelSettings;
  setSettings: Dispatch<SetStateAction<ModelSettings>>;
  ready: boolean;
  selectedPart?: ModelPartId | null;
  onSelectPart?: (id: ModelPartId, fit?: boolean) => void;
}
export default function ModelControls({ settings, setSettings, ready, selectedPart, onSelectPart }: Props) {
  return <aside className="sidebar" aria-label="模型控制">
    <section>
      <h2>部件显示</h2>
      <PartTree settings={settings} setSettings={setSettings} ready={ready}
        selectedPart={selectedPart} onSelectPart={onSelectPart} />
    </section>
    <section>
      <h2>剖切</h2>
      <label className="switch-control">
        <input type="checkbox" role="switch" aria-label="启用剖切" checked={settings.cutaway} disabled={!ready}
          onChange={e => setSettings(s => ({ ...s, cutaway: e.target.checked }))} />
        <span className="switch-track" aria-hidden="true" />
      </label>
      <div className={settings.cutaway ? 'cut-controls' : 'cut-controls inactive'}>
        <label htmlFor="cut-height">剖切高度</label>
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
