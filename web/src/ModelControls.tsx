import type { Dispatch, SetStateAction } from 'react';
import { activePreset, clampCutHeight, groups, presets, settingsForPreset } from './model-state';
import type { ModelSettings, PresetId } from './model-state';
import Parameters from './Parameters';

interface Props {
  settings: ModelSettings;
  setSettings: Dispatch<SetStateAction<ModelSettings>>;
  ready: boolean;
  onPreset: (id: PresetId) => void;
}
export default function ModelControls({ settings, setSettings, ready, onPreset }: Props) {
  return <aside className="sidebar" aria-label="模型控制">
    <section>
      <h2>模型视图</h2>
      <div className="presets">
        {presets.map(p => <button key={p.id} type="button" disabled={!ready}
          className={activePreset(settings) === p.id ? 'preset selected' : 'preset'}
          aria-pressed={activePreset(settings) === p.id} onClick={() => {
            setSettings(settingsForPreset(p.id)); onPreset(p.id);
          }}>{p.label}</button>)}
      </div>
    </section>
    <section>
      <h2>部件显示</h2>
      <div className="part-list">
        {groups.map(g => <label key={g.id} className="part-row">
          <input type="checkbox" checked={settings.visibility[g.id]} disabled={!ready}
            onChange={e => setSettings(s => ({ ...s, visibility: { ...s.visibility, [g.id]: e.target.checked } }))} />
          <span>{g.label}</span>
        </label>)}
      </div>
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
