import type { Dispatch, SetStateAction } from 'react';
import { activePreset, presets, settingsForPreset } from './model-state';
import type { ModelSettings, PresetId } from './model-state';
import { useLanguage } from './LanguageContext';

interface Props {
  settings: ModelSettings;
  setSettings: Dispatch<SetStateAction<ModelSettings>>;
  ready: boolean;
  onPreset: (id: PresetId) => void;
}

export default function ViewPresets({ settings, setSettings, ready, onPreset }: Props) {
  const { copy } = useLanguage();
  const active = activePreset(settings);
  return <div className="view-presets" role="group" aria-label={copy.presets.region}>
    {presets.map(p => <button key={p.id} type="button" disabled={!ready}
      className={active === p.id ? 'preset selected' : 'preset'}
      aria-pressed={active === p.id} onClick={() => {
        setSettings(settingsForPreset(p.id)); onPreset(p.id);
      }}>{copy.presets[p.id]}</button>)}
  </div>;
}
