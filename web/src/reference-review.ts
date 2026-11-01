export interface ReferenceAlignment { opacity: number; scale: number; x: number; y: number; rotation: number }
export const defaultReferenceAlignment: ReferenceAlignment = { opacity: .5, scale: 1, x: 0, y: 0, rotation: 0 };
export const referenceLimits = { opacity: [0, 1], scale: [.25, 4], x: [-100, 100], y: [-100, 100], rotation: [-180, 180] } as const;
export function referenceAlignment(value: Partial<ReferenceAlignment>): ReferenceAlignment {
  return Object.fromEntries(Object.entries(defaultReferenceAlignment).map(([name, fallback]) => {
    const key = name as keyof ReferenceAlignment, input = value[key], [min, max] = referenceLimits[key];
    return [key, typeof input === 'number' && Number.isFinite(input) ? Math.max(min, Math.min(max, input)) : fallback];
  })) as unknown as ReferenceAlignment;
}
export function validReferenceImage(file: { type: string; size: number }): boolean {
  return ['image/png', 'image/jpeg', 'image/webp'].includes(file.type) && file.size > 0 && file.size <= 12 * 1024 * 1024;
}
export function validReferenceDimensions(width: number, height: number): boolean {
  return [width, height].every(n => Number.isInteger(n) && n > 0 && n <= 16384) && width * height <= 32_000_000;
}
export function referenceTransform(value: ReferenceAlignment): string {
  const a = referenceAlignment(value);
  return `translate(${a.x}%, ${a.y}%) rotate(${a.rotation}deg) scale(${a.scale})`;
}
export function referenceImageRect(width: number, height: number, imageWidth: number, imageHeight: number, value: ReferenceAlignment) {
  if (![width, height, imageWidth, imageHeight].every(n => Number.isFinite(n) && n > 0)) throw new Error('Invalid reference image dimensions.');
  const a = referenceAlignment(value), fit = Math.min(width / imageWidth, height / imageHeight) * a.scale;
  return { centerX: width * (.5 + a.x / 100), centerY: height * (.5 + a.y / 100), width: imageWidth * fit, height: imageHeight * fit, rotation: a.rotation * Math.PI / 180, opacity: a.opacity };
}
