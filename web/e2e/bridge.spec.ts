import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';

test.beforeEach(async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await page.addInitScript(() => { localStorage.setItem('text-cad.locale', 'en'); localStorage.setItem('text-cad.theme', 'light'); });
});

test('Seto twin bridges load, expose independent parts and retain all three drawing views', async ({ page }, info) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message)); page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  await page.goto('?model=seto-ohashi&view=3d&environment=day');
  const canvas = page.locator('.bridge-canvas canvas');
  await expect(page).toHaveTitle(/Seto Ohashi/); await expect(canvas).toHaveAttribute('data-model-ready', 'true');
  await expect(canvas).toHaveAttribute('data-model-revision', 'BRIDGE-R04');
  await expect.poll(async () => Number(await canvas.getAttribute('data-render-triangles'))).toBeGreaterThan(0);
  await expect.poll(async () => Number(await canvas.getAttribute('data-render-calls'))).toBeLessThan(100);
  await expect(page.getByText('1,538 m', { exact: true })).toBeAttached();
  for (const [label, camera] of [['Side', 'elevation'], ['Top', 'top'], ['Tower close-up', 'tower'], ['Road–rail close-up', 'deck'], ['Follow vehicles', 'traffic'], ['Follow cruise boat', 'vessel'], ['Follow train', 'train']]) {
    await page.getByRole('button', { name: label, exact: true }).click();
    await canvas.scrollIntoViewIfNeeded(); await expect(canvas).toHaveAttribute('data-camera-view', camera);
    await expect.poll(async () => Number(await canvas.getAttribute('data-render-triangles'))).toBeGreaterThan(0);
  }
  await page.getByRole('button', { name: 'Road–rail close-up', exact: true }).click(); await canvas.scrollIntoViewIfNeeded();
  await info.attach('seto-road-rail-closeup', { body: await canvas.screenshot(), contentType: 'image/png' });
  const truss = page.getByRole('checkbox', { name: 'Stiffening truss', exact: true });
  await truss.uncheck(); await expect(canvas).toHaveAttribute('data-visible-groups', /^((?!truss).)*$/); await truss.check();
  await page.getByRole('button', { name: 'Twin-bridge overview', exact: true }).click();
  await page.getByRole('button', { name: 'Night', exact: true }).click(); await expect(canvas).toHaveAttribute('data-environment', 'night');
  await page.getByRole('button', { name: 'Day', exact: true }).click();
  for (const [locale, label, train, waves] of [['ja', '双子橋の全景', '電車を追う', '水面の波'], ['zh', '双桥全景', '电车跟随近景', '水面波动'], ['en', 'Twin-bridge overview', 'Follow train', 'Water animation']]) {
    await page.locator('.language-control select').selectOption(locale); await expect(page.getByRole('button', { name: label, exact: true })).toBeVisible();
    await expect(canvas).toHaveAttribute('data-model-ready', 'true');
    await expect(page.getByRole('button', { name: train, exact: true })).toBeAttached(); await expect(page.getByRole('checkbox', { name: waves, exact: true })).toBeAttached();
  }
  for (const view of ['Plan', 'Elevation', 'Cross-section']) {
    await page.getByRole('button', { name: view, exact: true }).click();
    const drawing = page.locator('.bridge-drawing:not([hidden]) img');
    await expect(drawing).toBeVisible(); await expect.poll(async () => drawing.evaluate(image => (image as HTMLImageElement).complete && (image as HTMLImageElement).naturalWidth > 0)).toBeTruthy();
  }
  await page.getByRole('button', { name: '3D model', exact: true }).click(); await canvas.scrollIntoViewIfNeeded();
  await expect(canvas).toHaveAttribute('data-camera-view', 'iso'); await expect(page.locator('vite-error-overlay')).toHaveCount(0); await expect(page.locator('[role="alert"]')).toHaveCount(0);
  await info.attach('seto-overview', { body: await canvas.screenshot(), contentType: 'image/png' });
  await info.attach('seto-renderer', { body: JSON.stringify(await canvas.evaluate(element => ({ ...(element as HTMLCanvasElement).dataset })), null, 2), contentType: 'application/json' });
  expect(errors).toEqual([]);
});

test('Seto native CAD and 3D downloads reconstruct exact released files', async ({ page }, info) => {
  test.skip(info.project.name === 'mobile', 'Native bytes are checked once; mobile viewer and drawings are covered separately.');
  await page.goto('?model=seto-ohashi&view=files');
  await expect(page.getByRole('heading', { name: 'Bridge CAD, 3D models and parametric sources', exact: true })).toBeVisible();
  for (const file of ['GLB/seto_ohashi.glb', 'STEP/seto_ohashi.step', 'DXF/seto_ohashi_section.dxf']) {
    const pending = page.waitForEvent('download'); await page.locator(`[data-file="${file}"] .download-row`).click();
    const download = await pending; expect(download.suggestedFilename()).toBe(file.split('/').at(-1));
    const saved = await readFile((await download.path())!), native = await readFile(new URL(`../../${file}`, import.meta.url));
    expect(createHash('sha256').update(saved).digest('hex')).toBe(createHash('sha256').update(native).digest('hex'));
  }
  await page.locator('#model-choice').selectOption('house'); await expect(page).toHaveURL(/model=house/);
  await page.locator('#model-choice').selectOption('seto-ohashi'); await expect(page).toHaveURL(/model=seto-ohashi/);
  await expect(page.locator('.bridge-canvas canvas')).toHaveAttribute('data-model-ready', 'true');
});

test('Seto drawing entry preloads the model and fits it when the 3D tab is first revealed', async ({ page }) => {
  await page.goto('?model=seto-ohashi&view=plan');
  const canvas = page.locator('.bridge-canvas canvas');
  await expect(canvas).toHaveAttribute('data-model-ready', 'true');
  await expect(canvas).toHaveAttribute('data-render-visibility', 'layout-hidden');
  await page.getByRole('button', { name: '3D model', exact: true }).click();
  await canvas.scrollIntoViewIfNeeded();
  await expect(canvas).toHaveAttribute('data-camera-view', 'iso');
  await expect.poll(async () => Number(await canvas.getAttribute('data-render-triangles'))).toBeGreaterThan(0);
  await expect(page.locator('[role="alert"]')).toHaveCount(0);
});

test('boats and left-hand traffic move independently, pause, and stop hidden work', async ({ page }, info) => {
  await page.goto('?model=seto-ohashi&view=3d');
  const canvas = page.locator('.bridge-canvas canvas');
  await expect(canvas).toHaveAttribute('data-model-ready', 'true'); await canvas.scrollIntoViewIfNeeded();
  await expect(canvas).toHaveAttribute('data-motion-state', 'playing');
  await expect(canvas).toHaveAttribute('data-actor-count', '36');
  const poses = async () => JSON.parse((await canvas.getAttribute('data-actor-poses'))!);
  await expect.poll(async () => !!(await canvas.getAttribute('data-actor-poses'))).toBeTruthy();
  const initial = await poses();
  await expect.poll(async () => (await poses()).traffic[0]).not.toBe(initial.traffic[0]);
  await expect.poll(async () => (await poses()).vessels[2]).not.toBe(initial.vessels[2]);
  expect((await poses()).vessels[0]).toBe(initial.vessels[0]);
  await expect.poll(async () => (await poses()).trains[0]).not.toBe(initial.trains[0]);
  const trainPoses = async () => JSON.parse((await canvas.getAttribute('data-train-poses'))!);
  const assertTrainSpacing = async () => {
    const carriages = await trainPoses(); expect(carriages).toHaveLength(8);
    for (const id of new Set(carriages.map((car: { train: string }) => car.train))) {
      const consist = carriages.filter((car: { train: string }) => car.train === id).sort((a: { index: number }, b: { index: number }) => a.index-b.index);
      expect(consist).toHaveLength(4);
      for (let i=1;i<consist.length;i++) expect(Math.abs(consist[i].position[0]-consist[i-1].position[0])).toBeCloseTo(20.5, 5);
    }
  };
  await assertTrainSpacing();
  if (initial.vessels[2] > 0) await expect.poll(async () => (await poses()).vessels[2], { timeout: 60_000 }).toBeLessThan(0);
  expect((await poses()).vessels[0]).toBe(initial.vessels[0]);
  await page.getByRole('button', { name: 'Follow vehicles', exact: true }).click(); await canvas.scrollIntoViewIfNeeded();
  await expect(canvas).toHaveAttribute('data-camera-view', 'traffic');
  await expect(canvas).toHaveAttribute('data-following-actor', /.+/);
  await info.attach('seto-moving-vehicle-closeup', { body: await canvas.screenshot(), contentType: 'image/png' });
  await page.getByRole('button', { name: 'Follow cruise boat', exact: true }).click(); await canvas.scrollIntoViewIfNeeded();
  await expect(canvas).toHaveAttribute('data-camera-view', 'vessel');
  await info.attach('seto-cruise-boat-closeup', { body: await canvas.screenshot(), contentType: 'image/png' });
  const profile = JSON.parse((await canvas.getAttribute('data-water-profile'))!); expect(profile.animatedNormals).toBe(true); expect(profile.distanceFiltered).toBe(true);
  const beforeWater = Number(await canvas.getAttribute('data-water-time'));
  await expect.poll(async () => Number(await canvas.getAttribute('data-water-time'))).toBeGreaterThan(beforeWater);
  await page.getByRole('button', { name: 'Follow train', exact: true }).click(); await canvas.scrollIntoViewIfNeeded();
  await expect(canvas).toHaveAttribute('data-camera-view', 'train'); await assertTrainSpacing();
  await info.attach('seto-moving-train-closeup', { body: await canvas.screenshot(), contentType: 'image/png' });
  const area = (await canvas.boundingBox())!;
  await page.mouse.move(area.x + area.width / 2, area.y + area.height / 2); await page.mouse.down();
  await page.mouse.move(area.x + area.width / 2 + 50, area.y + area.height / 2 + 15, { steps: 4 }); await page.mouse.up();
  await expect(canvas).toHaveAttribute('data-following-actor', '');
  await page.getByRole('button', { name: 'Pause traffic animation', exact: true }).click(); await canvas.scrollIntoViewIfNeeded();
  await expect(canvas).toHaveAttribute('data-motion-state', 'paused'); await expect(canvas).toHaveAttribute('data-render-state', 'idle');
  const paused = await poses(), pausedWater = await canvas.getAttribute('data-water-time'), pausedTrain = await trainPoses();
  await page.waitForTimeout(1200); expect(await poses()).toEqual(paused); expect(await canvas.getAttribute('data-water-time')).toBe(pausedWater); expect(await trainPoses()).toEqual(pausedTrain);
  await page.getByRole('button', { name: 'Play traffic animation', exact: true }).click(); await canvas.scrollIntoViewIfNeeded();
  await expect(canvas).toHaveAttribute('data-motion-state', 'playing');
  await expect.poll(async () => (await poses()).traffic[0]).not.toBe(paused.traffic[0]);
  const resumed = await poses(); expect(Math.abs(resumed.traffic[0] - paused.traffic[0])).toBeLessThan(12);
  for (const label of ['Moving vehicles', 'Cruise boats', 'Railway trains']) await page.getByRole('checkbox', { name: label, exact: true }).uncheck();
  await canvas.scrollIntoViewIfNeeded(); await expect(canvas).toHaveAttribute('data-motion-state', 'playing');
  const waterAlone = Number(await canvas.getAttribute('data-water-time'));
  await expect.poll(async () => Number(await canvas.getAttribute('data-water-time'))).toBeGreaterThan(waterAlone);
  await page.getByRole('checkbox', { name: 'Water animation', exact: true }).uncheck(); await canvas.scrollIntoViewIfNeeded();
  await expect(canvas).toHaveAttribute('data-motion-state', 'inactive-groups');
  await expect(canvas).toHaveAttribute('data-render-state', 'idle'); const hidden = await poses();
  await page.getByRole('checkbox', { name: 'Cruise boats', exact: true }).check(); await canvas.scrollIntoViewIfNeeded();
  await expect.poll(async () => (await poses()).vessels[2]).not.toBe(hidden.vessels[2]);
  expect((await poses()).traffic).toEqual(hidden.traffic);
  await page.getByRole('button', { name: 'Plan', exact: true }).click();
  await expect(canvas).toHaveAttribute('data-motion-state', 'hidden');
  const inactive = await canvas.getAttribute('data-actor-poses'), inactiveWater = await canvas.getAttribute('data-water-time');
  await page.waitForTimeout(250); expect(await canvas.getAttribute('data-actor-poses')).toBe(inactive); expect(await canvas.getAttribute('data-water-time')).toBe(inactiveWater);
});

test('reduced-motion starts at the native static pose and accepts an explicit play action', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' }); await page.goto('?model=seto-ohashi&view=3d');
  const canvas = page.locator('.bridge-canvas canvas'); await expect(canvas).toHaveAttribute('data-model-ready', 'true'); await canvas.scrollIntoViewIfNeeded();
  await expect(canvas).toHaveAttribute('data-motion-state', 'paused'); await expect(canvas).toHaveAttribute('data-render-state', 'idle');
  const pose = await canvas.getAttribute('data-actor-poses'); await expect(canvas).toHaveAttribute('data-water-time', '0.000');
  await page.waitForTimeout(250); expect(await canvas.getAttribute('data-actor-poses')).toBe(pose); await expect(canvas).toHaveAttribute('data-water-time', '0.000');
  await expect(page.getByText(/Your reduced-motion preference pauses/)).toBeAttached();
  await page.getByRole('button', { name: 'Play traffic animation', exact: true }).click(); await canvas.scrollIntoViewIfNeeded();
  await expect(canvas).toHaveAttribute('data-motion-state', 'playing');
  await expect.poll(async () => canvas.getAttribute('data-actor-poses')).not.toBe(pose);
});


test('procedural water changes rendered pixels, freezes independently, and switches to night colours', async ({ page }, info) => {
  await page.goto('?model=seto-ohashi&view=3d&environment=day');
  const canvas = page.locator('.bridge-canvas canvas'); await expect(canvas).toHaveAttribute('data-model-ready', 'true');
  await page.getByRole('button', { name: 'Follow cruise boat', exact: true }).click();
  for (const label of ['Moving vehicles', 'Cruise boats', 'Railway trains']) await page.getByRole('checkbox', { name: label, exact: true }).uncheck();
  await canvas.scrollIntoViewIfNeeded(); await expect(canvas).toHaveAttribute('data-motion-state', 'playing');
  const first = await canvas.screenshot(), firstTime = Number(await canvas.getAttribute('data-water-time'));
  await expect.poll(async () => Number(await canvas.getAttribute('data-water-time'))).toBeGreaterThan(firstTime + .3);
  expect(await canvas.screenshot()).not.toEqual(first);
  await page.getByRole('checkbox', { name: 'Water animation', exact: true }).uncheck(); await canvas.scrollIntoViewIfNeeded();
  await expect(canvas).toHaveAttribute('data-render-state', 'idle'); const stoppedTime = await canvas.getAttribute('data-water-time');
  const stopped = await canvas.screenshot(); await page.waitForTimeout(300);
  expect(await canvas.getAttribute('data-water-time')).toBe(stoppedTime); expect(await canvas.screenshot()).toEqual(stopped);
  await info.attach('seto-water-day-static', { body: stopped, contentType: 'image/png' });
  await page.getByRole('button', { name: 'Night', exact: true }).click(); await canvas.scrollIntoViewIfNeeded();
  await expect(canvas).toHaveAttribute('data-render-state', 'idle'); const night = await canvas.screenshot(); expect(night).not.toEqual(stopped);
  await info.attach('seto-water-night-static', { body: night, contentType: 'image/png' });
});
