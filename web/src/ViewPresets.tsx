import type { Dispatch, SetStateAction } from 'react';
import { activePreset, presets, settingsForPreset } from './model-state';
import type { ModelSettings, PresetId } from './model-state';

interface Props {
  settings: ModelSettings;
  setSettings: Dispatch<SetStateAction<ModelSettings>>;
  ready: boolean;
  onPreset: (id: PresetId) => void;
}

export default function ViewPresets({ settings, setSettings, ready, onPreset }: Props) {
  const active = activePreset(settings);
  return <div className="view-presets" role="group" aria-label="模型视图">
    {presets.map(p => <button key={p.id} type="button" disabled={!ready}
      className={active === p.id ? 'preset selected' : 'preset'}
      aria-pressed={active === p.id} onClick={() => {
        setSettings(settingsForPreset(p.id)); onPreset(p.id);
      }}>{p.label}</button>)}
  </div>;
}
