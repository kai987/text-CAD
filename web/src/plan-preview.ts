import metadata from './plan-preview-metadata.json' with { type: 'json' };

export type PlanView = 'plan' | 'sheet';
export const planPreviews = metadata.floors;

export function planViewBox(floor: 1 | 2, view: PlanView) {
  const preview = planPreviews.find(item => item.floor === floor)!;
  return view === 'plan' ? preview.planViewBox : preview.fullViewBox;
}

export function fittedPlanWidth(viewBox: number[], availableWidth: number, availableHeight: number) {
  return Math.max(1, Math.min(availableWidth, availableHeight * viewBox[2] / viewBox[3]));
}
