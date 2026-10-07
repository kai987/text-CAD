import test from 'node:test';
import assert from 'node:assert/strict';
import { createDemandRenderScheduler } from '../src/demand-render.ts';

function frameQueue() {
  let id = 0;
  const callbacks = new Map();
  return {
    requestFrame(callback) { const next = ++id; callbacks.set(next, callback); return next; },
    cancelFrame(id) { callbacks.delete(id); },
    tick() { const batch = [...callbacks]; callbacks.clear(); batch.forEach(([, callback]) => callback(0)); },
    get pending() { return callbacks.size; },
  };
}

test('scene changes share one frame and a settled scene has no queued work', () => {
  const queue = frameQueue();
  let frames = 0;
  let state;
  const scheduler = createDemandRenderScheduler({ ...queue, draw: () => frames++, onState: value => { state = value; } });
  for (let i = 0; i < 100; i++) scheduler.invalidate();
  assert.equal(queue.pending, 1);
  assert.equal(state, 'scheduled');
  queue.tick();
  assert.equal(frames, 1);
  assert.equal(queue.pending, 0);
  assert.equal(state, 'idle');
});

test('damping changes during drawing schedule only the necessary follow-up frames', () => {
  const queue = frameQueue();
  let frames = 0;
  const scheduler = createDemandRenderScheduler({ ...queue, draw() {
    frames++;
    if (frames < 3) { scheduler.invalidate(); scheduler.invalidate(); }
  } });
  scheduler.invalidate();
  queue.tick(); queue.tick(); queue.tick();
  assert.equal(frames, 3);
  assert.equal(queue.pending, 0);
});

test('hidden scenes cancel queued work and resume once with the latest scene state', () => {
  const queue = frameQueue();
  let scene = 'day';
  const rendered = [];
  let state;
  const scheduler = createDemandRenderScheduler({ ...queue, draw: () => rendered.push(scene), onState: value => { state = value; } });
  scheduler.invalidate(); scheduler.setActive(false);
  assert.equal(queue.pending, 0);
  assert.equal(state, 'paused');
  for (const next of ['night', 'selected', 'sectioned']) { scene = next; scheduler.invalidate(); }
  queue.tick();
  assert.deepEqual(rendered, []);
  scheduler.setActive(true); scheduler.setActive(true);
  assert.equal(queue.pending, 1);
  queue.tick();
  assert.deepEqual(rendered, ['sectioned']);
  assert.equal(state, 'idle');
  scheduler.setActive(false); scheduler.setActive(true); queue.tick();
  assert.deepEqual(rendered, ['sectioned', 'sectioned'], 'revealing an unchanged canvas refreshes it once');
});

test('disposing cancels queued work and ignores future scene or visibility changes', () => {
  const queue = frameQueue();
  let frames = 0;
  let state;
  const scheduler = createDemandRenderScheduler({ ...queue, draw: () => frames++, onState: value => { state = value; } });
  scheduler.invalidate(); scheduler.dispose(); scheduler.dispose();
  scheduler.invalidate(); scheduler.setActive(false); scheduler.setActive(true); queue.tick();
  assert.equal(frames, 0);
  assert.equal(queue.pending, 0);
  assert.equal(state, 'disposed');
});
