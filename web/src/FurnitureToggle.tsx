import { useEffect, useRef } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import { furnitureVisibilityState, setFurnitureVisible } from './model-state';
import type { ModelSettings } from './model-state';
import { useModel } from './ModelContext';

export default function FurnitureToggle({ settings, setSettings, ready }: {
  settings: ModelSettings; setSettings: Dispatch<SetStateAction<ModelSettings>>; ready: boolean;
}) {
  const { copy, layout } = useModel();
  const ref = useRef<HTMLInputElement>(null);
  const state = furnitureVisibilityState(settings, layout);
  useEffect(() => { if (ref.current) ref.current.indeterminate = state === 'some'; }, [state]);
  return <label className="furniture-toggle" title={copy.controls.furnitureHelp}>
    <input ref={ref} type="checkbox" checked={state === 'all'} disabled={!ready}
      onChange={event => setSettings(previous => setFurnitureVisible(previous, event.target.checked, layout))} />
    <span>{copy.controls.showFurniture}</span>
  </label>;
}
