import type { Dispatch, SetStateAction } from 'react';
import { Moon, Sun } from 'lucide-react';
import type { ModelSettings } from './model-state';
import { useModel } from './ModelContext';

interface Props {
  settings: ModelSettings;
  setSettings: Dispatch<SetStateAction<ModelSettings>>;
  ready: boolean;
}

export default function SceneLightingControls({ settings, setSettings, ready }: Props) {
  const { copy, layout } = useModel();
  return <div className="scene-lighting-controls">
    <div className="scene-environment" role="group" aria-label={copy.sceneLighting.label} title={copy.sceneLighting.help}>
      <span className="scene-lighting-label">{copy.sceneLighting.label}</span>
      <button type="button" className={settings.environment === 'day' ? 'scene-time selected' : 'scene-time'}
        aria-pressed={settings.environment === 'day'} disabled={!ready}
        onClick={() => setSettings(previous => ({ ...previous, environment: 'day' }))}>
        <Sun size={16} aria-hidden="true" />{copy.sceneLighting.day}
      </button>
      <button type="button" className={settings.environment === 'night' ? 'scene-time selected' : 'scene-time'}
        aria-pressed={settings.environment === 'night'} disabled={!ready}
        onClick={() => setSettings(previous => ({ ...previous, environment: 'night' }))}>
        <Moon size={16} aria-hidden="true" />{copy.sceneLighting.night}
      </button>
    </div>
    {layout.id === 'house' ? <label className="scene-outdoor-lights" title={copy.sceneLighting.fixtureHelp}>
      <span>{copy.sceneLighting.outdoor}</span>
      <span className="switch-control">
        <input type="checkbox" role="switch" aria-label={copy.sceneLighting.outdoor}
          checked={settings.outdoorLights} disabled={!ready}
          onChange={event => setSettings(previous => ({ ...previous, outdoorLights: event.target.checked }))} />
        <span className="switch-track" aria-hidden="true" />
      </span>
    </label> : null}
    {layout.id === 'house' ? <label className="scene-outdoor-lights" title={copy.sceneLighting.indoorHelp}>
      <span>{copy.sceneLighting.indoor}</span><span className="switch-control">
        <input type="checkbox" role="switch" aria-label={copy.sceneLighting.indoor} checked={settings.indoorLights} disabled={!ready}
          onChange={event => setSettings(previous => ({ ...previous, indoorLights: event.target.checked }))} />
        <span className="switch-track" aria-hidden="true" />
      </span>
    </label> : null}
    <p className="scene-lighting-help">{layout.id === 'house' ? copy.sceneLighting.fixtureHelp : copy.sceneLighting.help}</p>
  </div>;
}
