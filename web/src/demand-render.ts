export type DemandRenderState = 'idle' | 'scheduled' | 'paused' | 'disposed';

interface Options {
  draw: () => void;
  requestFrame: (callback: FrameRequestCallback) => number;
  cancelFrame: (id: number) => void;
  onState?: (state: DemandRenderState) => void;
}

/** Coalesce scene changes, including changes emitted by OrbitControls while drawing. */
export function createDemandRenderScheduler({ draw, requestFrame, cancelFrame, onState }: Options) {
  let active = true;
  let disposed = false;
  let dirty = false;
  let drawing = false;
  let frame: number | null = null;

  function report() {
    onState?.(disposed ? 'disposed' : !active ? 'paused' : frame !== null ? 'scheduled' : 'idle');
  }
  function schedule() {
    if (!disposed && active && dirty && !drawing && frame === null) frame = requestFrame(flush);
  }
  function flush() {
    frame = null;
    if (disposed || !active) return;
    dirty = false;
    drawing = true;
    try { draw(); }
    finally { drawing = false; schedule(); report(); }
  }
  report();
  return {
    invalidate() {
      if (disposed) return;
      dirty = true; schedule(); report();
    },
    setActive(next: boolean) {
      if (disposed || active === next) return;
      active = next;
      if (!active && frame !== null) { cancelFrame(frame); frame = null; }
      // A revealed canvas needs one fresh frame even when the hidden scene stayed unchanged.
      if (active) { dirty = true; schedule(); }
      report();
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      if (frame !== null) cancelFrame(frame);
      frame = null; dirty = false; report();
    },
  };
}
